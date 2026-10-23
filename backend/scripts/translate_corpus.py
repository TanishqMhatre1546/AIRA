"""Offline clinical guideline translation tool with automated safety checks."""

import argparse
import csv
import difflib
import json
import logging
import re
import sys
from pathlib import Path
from typing import Any

# Ensure backend root is in sys.path
backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app.config import settings  # noqa: E402
from app.core.text import DEVANAGARI_DIGITS  # noqa: E402
from app.data.corpus_loader import (  # noqa: E402
    extract_provenance_items_from_doc,
    load_condition_documents,
)
from app.data.models import ConditionDocument  # noqa: E402
from app.data.translations import compute_source_hash  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Devanagari Unicode character range
DEVANAGARI_CHAR_REGEX = re.compile(r"[\u0900-\u097F]")

# Prohibited dosing keywords in Hindi and Marathi
PROHIBITED_DOSE_REGEX = re.compile(
    r"\b(?:\d+\s*(?:mg|mcg|iu|मिलीग्राम|एमजी|मिली|लीटर|गोली|गोलियां|गोळ्या|गोळी|खुराक|कॅप्सूल))\b|"
    r"(?:दवा\s+की\s+खुराक|दवा\s+की\s+मात्रा|औषधाचा\s+डोस|औषधाची\s+मात्रा)",
    re.IGNORECASE,
)

# Prohibited diagnosis statements
PROHIBITED_DIAGNOSIS_REGEX = re.compile(
    r"(?:आपको\s+.*?(?:है|हो\s+गया|हो\s+सकता\s+है)|"
    r"तुमको\s+.*?(?:है|हो\s+गया)|"
    r"तुम्हाला\s+.*?(?:आहे|झाले\s+आहे|झाला\s+आहे)|"
    r"निदान\s*:|रोगनिदान|बीमारी\s+का\s+निदान)",
    re.IGNORECASE,
)


def extract_numbers_from_text(text: str) -> set[str]:
    """Extract all integer and floating point numbers after digit normalization."""
    normalized = text.translate(DEVANAGARI_DIGITS)
    matches = re.findall(r"\b\d+(?:\.\d+)?\b", normalized)
    return set(matches)


def check_number_and_unit_preservation(source_en: str, translation: str) -> list[str]:
    """Check that all numbers, units, and critical thresholds are preserved."""
    flags: list[str] = []
    source_nums = extract_numbers_from_text(source_en)
    trans_nums = extract_numbers_from_text(translation)

    missing_nums = source_nums - trans_nums
    for num in sorted(missing_nums):
        flags.append(f"missing_number:{num}")

    # Check key critical terms when present in source
    source_lower = source_en.lower()
    trans_normalized = translation.translate(DEVANAGARI_DIGITS).lower()

    if re.search(r"\b112\b", source_en) and "112" not in trans_normalized:
        flags.append("missing_emergency_number_112")
    if re.search(r"\bors\b", source_lower):
        if not any(k in translation for k in ("ORS", "ors", "ओआरएस", "ओ.आर.एस.")):
            flags.append("missing_acronym_ors")
    if re.search(r"\bbp\b", source_lower):
        if not any(k in translation for k in ("BP", "bp", "बीपी", "रक्तचाप", "रक्तदाब")):
            flags.append("missing_acronym_bp")

    return flags


def check_script_and_length(source_en: str, translation: str) -> list[str]:
    """Check that translation is mostly Devanagari and has reasonable length."""
    flags: list[str] = []
    clean_trans = re.sub(r"[\s\d\W_]+", "", translation)
    if clean_trans:
        devanagari_chars = len(DEVANAGARI_CHAR_REGEX.findall(clean_trans))
        # If source has preserved Latin terms (like degrees Fahrenheit, ORS, BP), allow Latin
        source_latin = len(re.findall(r"[A-Za-z]", source_en))
        min_ratio = 0.30 if source_latin > 10 else 0.50
        ratio = devanagari_chars / len(clean_trans)
        if ratio < min_ratio:
            flags.append(f"low_devanagari_ratio:{ratio:.2f}")

    len_src = len(source_en.strip())
    len_trans = len(translation.strip())
    if len_src > 20:
        ratio = len_trans / len_src
        if ratio < 0.35:
            flags.append(f"translation_too_short:{ratio:.2f}")
        elif ratio > 3.0:
            flags.append(f"translation_too_long:{ratio:.2f}")
    elif len_src > 0 and len_trans > 120:
        flags.append(f"translation_too_long:{len_trans}")

    return flags


def check_dosing_and_diagnosis(
    source_en: str, translation: str, _lang: str
) -> list[str]:
    """Check for introduced dosing patterns or direct diagnosis assertions."""
    flags: list[str] = []

    # Prohibited diagnosis check
    if PROHIBITED_DIAGNOSIS_REGEX.search(translation):
        flags.append("prohibited_diagnosis_statement")

    # Dosing check: if translation has dosing tokens not justified by source
    trans_dose_matches = PROHIBITED_DOSE_REGEX.findall(translation)
    if trans_dose_matches:
        source_has_numbers = bool(extract_numbers_from_text(source_en))
        if not source_has_numbers:
            flags.append("forbidden_dose_pattern")

    return flags


def compute_similarity(text1: str, text2: str) -> float:
    """Compute normalized sequence similarity ratio between two texts."""
    clean1 = " ".join(text1.lower().split())
    clean2 = " ".join(text2.lower().split())
    return difflib.SequenceMatcher(None, clean1, clean2).ratio()


def check_backtranslation(source_en: str, back_trans: str) -> list[str]:
    """Check similarity between original English source and back-translation."""
    flags: list[str] = []
    similarity = compute_similarity(source_en, back_trans)
    if similarity < 0.30:
        flags.append(f"low_backtranslation_similarity:{similarity:.2f}")
    return flags


class GuidelineTranslator:
    """Offline translator with safety validation for Indian clinical guidelines."""

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or (
            settings.gemini_api_key.get_secret_value()
            if settings.gemini_api_key
            else None
        )
        self._llm: Any = None

    def _get_llm(self) -> Any:
        if self._llm is None:
            if not self.api_key:
                raise ValueError("GEMINI_API_KEY is required to translate offline corpus.")
            from langchain_google_genai import ChatGoogleGenerativeAI

            self._llm = ChatGoogleGenerativeAI(
                model=settings.chat_model,
                google_api_key=self.api_key,
                temperature=0.0,
            )
        return self._llm

    def translate_item(self, text: str, lang: str) -> tuple[str, str]:
        """Translate clinical item text to target language and back to English."""
        llm = self._get_llm()
        lang_name = "Hindi" if lang == "hi" else "Marathi"

        prompt = (
            f"You are translating an official Indian clinical guideline item for general readers in India at a plain reading level.\n"
            f"Source English text: \"{text}\"\n"
            f"Target language: {lang_name} ({lang})\n\n"
            f"Strict rules:\n"
            f"1. Translate for a general reader at a plain reading level.\n"
            f"2. Keep every number, unit, and threshold exactly.\n"
            f"3. Do not add or remove advice.\n"
            f"4. Do not add any dose or medicine that is not in the source.\n"
            f"5. Keep medicine names that appear in the source (transliterated if usual).\n"
            f"6. Keep '112' and 'ORS' and 'BP' as they are.\n"
            f"7. Do not state a diagnosis (never say 'आपको ... है' or 'तुम्हाला ... आहे').\n"
            f"8. Output ONLY the translated text without commentary or formatting quotes."
        )

        resp = llm.invoke(prompt)
        translation = str(resp.content).strip().strip('"').strip("'")

        # Back-translation
        back_prompt = (
            f"Translate this medical guideline sentence back to English accurately and literally.\n"
            f"Text: \"{translation}\"\n"
            f"Output ONLY the English translation without quotes or extra commentary."
        )
        back_resp = llm.invoke(back_prompt)
        back_translation = str(back_resp.content).strip().strip('"').strip("'")

        return translation, back_translation


def process_corpus_translation(
    curated_dir: Path,
    i18n_dir: Path,
    reports_dir: Path,
    languages: list[str],
    condition_filter: str | None = None,
    dry_run: bool = False,
) -> None:
    """Translate all curated condition items and write sidecars and review CSVs."""
    i18n_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    docs = load_condition_documents(curated_dir)
    translator: GuidelineTranslator | None = None
    if not dry_run:
        translator = GuidelineTranslator()

    for lang in languages:
        csv_path = reports_dir / f"translation_review_{lang}.csv"
        csv_rows: list[dict[str, Any]] = []

        for doc in docs:
            cond_stem = doc.id.replace("icmr-stw-", "").replace("-", "_")
            if condition_filter and condition_filter not in (doc.id, cond_stem):
                continue

            sidecar_file = i18n_dir / f"{cond_stem}.{lang}.json"
            existing_data: dict[str, Any] = {}
            if sidecar_file.exists():
                try:
                    with open(sidecar_file, encoding="utf-8") as f:
                        existing_data = json.load(f)
                except Exception as e:
                    logger.warning("Could not read %s: %s", sidecar_file, e)

            existing_translations = existing_data.get("translations", {})
            updated_translations: dict[str, Any] = {}

            provenance_records = extract_provenance_items_from_doc(doc)
            logger.info("Processing %s (%s) [%d items] for lang=%s", doc.condition, cond_stem, len(provenance_records), lang)

            for rec in provenance_records:
                item_id = rec.item_id
                src_text = rec.text
                src_hash = compute_source_hash(src_text)

                existing_item = existing_translations.get(item_id, {})
                prev_text = existing_item.get("text", "")
                prev_status = existing_item.get("status", "draft")
                prev_src_hash = existing_item.get("source_hash")
                prev_reviewer = existing_item.get("reviewer")
                prev_reviewed_on = existing_item.get("reviewed_on")

                # If English item changed, reset translation to draft
                if prev_src_hash and prev_src_hash != src_hash:
                    logger.info("Source changed for %s in %s; resetting to draft", item_id, doc.id)
                    prev_status = "draft"
                    prev_reviewer = None
                    prev_reviewed_on = None

                translation = prev_text
                back_trans = existing_item.get("back_translation", "")

                if not translation and not dry_run and translator:
                    try:
                        translation, back_trans = translator.translate_item(src_text, lang)
                    except Exception as err:
                        logger.error("Failed translating item %s: %s", item_id, err)
                        translation = ""
                        back_trans = ""

                # Run automatic validation checks
                flags: list[str] = []
                if translation:
                    flags.extend(check_number_and_unit_preservation(src_text, translation))
                    flags.extend(check_script_and_length(src_text, translation))
                    flags.extend(check_dosing_and_diagnosis(src_text, translation, lang))
                    if back_trans:
                        flags.extend(check_backtranslation(src_text, back_trans))

                status = prev_status
                if flags:
                    status = "rejected"
                elif status not in ("draft", "reviewed"):
                    status = "draft"

                updated_translations[item_id] = {
                    "item_id": item_id,
                    "source_hash": src_hash,
                    "text": translation,
                    "back_translation": back_trans,
                    "status": status,
                    "reviewer": prev_reviewer,
                    "reviewed_on": prev_reviewed_on,
                    "flags": flags,
                }

                csv_rows.append(
                    {
                        "item_id": item_id,
                        "condition_id": doc.id,
                        "section_type": rec.section_type,
                        "English": src_text,
                        "translation": translation,
                        "back_translation": back_trans,
                        "flags": ";".join(flags),
                        "status": status,
                        "reviewer": prev_reviewer or "",
                        "reviewed_on": prev_reviewed_on or "",
                    }
                )

            # Write sidecar JSON
            sidecar_payload = {
                "condition_id": doc.id,
                "language": lang,
                "translations": updated_translations,
            }
            with open(sidecar_file, "w", encoding="utf-8") as f:
                json.dump(sidecar_payload, f, indent=2, ensure_ascii=False)
                f.write("\n")

        # Write reviewer CSV
        fieldnames = [
            "item_id",
            "condition_id",
            "section_type",
            "English",
            "translation",
            "back_translation",
            "flags",
            "status",
            "reviewer",
            "reviewed_on",
        ]
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_rows)
        logger.info("Wrote reviewer report: %s (%d rows)", csv_path, len(csv_rows))


def main() -> None:
    """CLI entrypoint for corpus translation tool."""
    parser = argparse.ArgumentParser(description="Translate curated guidelines for AIRA.")
    parser.add_argument("--lang", choices=["hi", "mr", "both"], default="both", help="Target language")
    parser.add_argument("--condition", default=None, help="Specific condition ID to translate")
    parser.add_argument("--dry-run", action="store_true", help="Run checks on existing translations without calling LLM")
    args = parser.parse_args()

    curated_dir = backend_root / "data" / "curated"
    i18n_dir = curated_dir / "i18n"
    reports_dir = backend_root / "reports"

    languages = ["hi", "mr"] if args.lang == "both" else [args.lang]
    process_corpus_translation(
        curated_dir=curated_dir,
        i18n_dir=i18n_dir,
        reports_dir=reports_dir,
        languages=languages,
        condition_filter=args.condition,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
