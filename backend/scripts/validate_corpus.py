"""Comprehensive validation script and manifest generator for the AIRA curated corpus."""

import csv
import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

# Ensure backend root is in sys.path
backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app.data.corpus_loader import normalize_text  # noqa: E402
from app.data.models import ConditionDocument, UrgencyRulesFile  # noqa: E402

ALLOWED_DRUG_NAMES = frozenset(
    {
        "paracetamol",
        "ibuprofen",
        "aspirin",
        "nsaid",
        "nsaids",
        "antihistamine",
        "antihistamines",
        "petroleum jelly",
        "liquid paraffin",
    }
)

DOSING_PROHIBITED_PATTERNS = [
    re.compile(r"\b\d+\s*(?:mg|mcg|iu)\b", re.IGNORECASE),
    re.compile(r"\b\d+\s*g\b", re.IGNORECASE),
    re.compile(
        r"\b(?:tablet|tablets|capsule|capsules|syrup|syrups|injection|injections|"
        r"twice daily|three times|bd|tds|qid|od)\b",
        re.IGNORECASE,
    ),
]

VOLUME_PATTERN = re.compile(
    r"\b\d+\s*(?:ml|litre|litres|liter|liters|glass|glasses)\b", re.IGNORECASE
)
ALLOWED_VOLUME_CONTEXTS = re.compile(
    r"\b(?:ors|water|fluid|fluids|salt|salts|liquid|drink|beverage)\b", re.IGNORECASE
)


def compute_file_sha256(path: Path) -> str:
    """Compute standard SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def load_drug_lexicon(lexicon_path: Path) -> list[str]:
    """Load forbidden drug names from lexicon, excluding allowed names."""
    if not lexicon_path.exists():
        return []
    forbidden: list[str] = []
    with open(lexicon_path, encoding="utf-8") as f:
        for line in f:
            clean = line.strip().lower()
            if clean and not clean.startswith("#") and clean not in ALLOWED_DRUG_NAMES:
                forbidden.append(clean)
    return sorted(forbidden, key=len, reverse=True)


class CorpusValidator:
    """Performs validation checks against clinical JSON files and urgency rules."""

    def __init__(self, curated_dir: Path, lexicon_path: Path) -> None:
        self.curated_dir = curated_dir
        self.lexicon_path = lexicon_path
        self.errors: list[str] = []
        self.forbidden_drugs = load_drug_lexicon(lexicon_path)
        self.known_condition_ids: set[str] = set()

    def add_error(self, check_num: int, location: str, message: str) -> None:
        self.errors.append(f"[Check {check_num}] [{location}] {message}")

    def check_em_dashes(self, obj: Any, location: str) -> None:
        """Check 6: Zero em dashes in any string."""
        if isinstance(obj, str):
            if "\u2014" in obj or "\\u2014" in obj:
                self.add_error(6, location, f"Contains em dash (U+2014): '{obj[:60]}...'")
        elif isinstance(obj, dict):
            for k, v in obj.items():
                self.check_em_dashes(v, f"{location}.{k}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                self.check_em_dashes(item, f"{location}[{i}]")

    def check_dosing_in_sentence(self, sentence: str, location: str) -> None:
        """Check 7: Dosing scan with volume exceptions."""
        for pat in DOSING_PROHIBITED_PATTERNS:
            match = pat.search(sentence)
            if match:
                self.add_error(
                    7,
                    location,
                    f"Prohibited dosing phrase '{match.group(0)}' in: '{sentence}'",
                )

        vol_match = VOLUME_PATTERN.search(sentence)
        if vol_match and not ALLOWED_VOLUME_CONTEXTS.search(sentence):
            self.add_error(
                7,
                location,
                f"Volume '{vol_match.group(0)}' without permitted fluid context in: '{sentence}'",
            )

    def check_drug_names(self, text: str, location: str) -> None:
        """Check 8: Drug-name scan."""
        for drug in self.forbidden_drugs:
            pattern = r"\b" + re.escape(drug) + r"\b"
            if re.search(pattern, text, re.IGNORECASE):
                self.add_error(8, location, f"Prohibited drug name '{drug}' found in: '{text}'")

    def validate_condition_file(self, path: Path) -> None:
        """Validate a single condition JSON document."""
        rel_loc = path.name
        try:
            with open(path, encoding="utf-8") as f:
                raw = json.load(f)
        except Exception as e:
            self.add_error(1, rel_loc, f"JSON syntax error: {e}")
            return

        self.check_em_dashes(raw, rel_loc)

        try:
            doc = ConditionDocument.model_validate(raw)
        except Exception as e:
            self.add_error(1, rel_loc, f"Schema validation failed: {e}")
            return

        self.known_condition_ids.add(doc.id)

        for s_idx, sec in enumerate(doc.sections):
            sec_loc = f"{rel_loc}.sections[{s_idx}]"
            seen_items: set[str] = set()

            if not sec.label.strip():
                self.add_error(2, sec_loc, "Section label is empty")

            if sec.page is None or not isinstance(sec.page, int) or sec.page < 0:
                self.add_error(3, sec_loc, f"Section page must be positive int, got: {sec.page}")

            if not sec.items:
                self.add_error(2, sec_loc, "Section has no items")

            for i_idx, itm in enumerate(sec.items):
                item_loc = f"{sec_loc}.items[{i_idx}]"
                if not itm.strip():
                    self.add_error(2, item_loc, "Item text is empty")
                    continue

                norm = normalize_text(itm)
                if norm in seen_items:
                    self.add_error(4, item_loc, f"Duplicate item: '{itm}'")
                seen_items.add(norm)

                self.check_dosing_in_sentence(itm, item_loc)
                self.check_drug_names(itm, item_loc)

        if doc.condition_description:
            if isinstance(doc.condition_description, str):
                self.check_dosing_in_sentence(
                    doc.condition_description, f"{rel_loc}.condition_description"
                )
                self.check_drug_names(doc.condition_description, f"{rel_loc}.condition_description")
            elif isinstance(doc.condition_description, dict):
                for k, v in doc.condition_description.items():
                    if isinstance(v, str):
                        self.check_dosing_in_sentence(v, f"{rel_loc}.condition_description.{k}")
                        self.check_drug_names(v, f"{rel_loc}.condition_description.{k}")

    def validate_urgency_rules(self, path: Path) -> None:
        """Validate urgency_rules.json file and cross-references."""
        rel_loc = path.name
        try:
            with open(path, encoding="utf-8") as f:
                raw = json.load(f)
        except Exception as e:
            self.add_error(1, rel_loc, f"JSON syntax error: {e}")
            return

        self.check_em_dashes(raw, rel_loc)

        try:
            rules_file = UrgencyRulesFile.model_validate(raw)
        except Exception as e:
            self.add_error(1, rel_loc, f"Urgency rules schema validation failed: {e}")
            return

        all_rules = (
            rules_file.emergency_rules + rules_file.see_doctor_rules + rules_file.self_care_rules
        )

        for rule in all_rules:
            rule_loc = f"{rel_loc}.rules[{rule.id}]"
            if rule.source_id is None:
                if rule.review_status != "pending_clinical_review":
                    self.add_error(
                        5,
                        rule_loc,
                        f"Rule {rule.id} has null source_id without pending status",
                    )
            elif rule.source_id not in self.known_condition_ids:
                self.add_error(
                    5,
                    rule_loc,
                    f"Rule {rule.id} has unknown source_id '{rule.source_id}'",
                )

            if rule.response:
                self.check_dosing_in_sentence(rule.response, f"{rule_loc}.response")
                self.check_drug_names(rule.response, f"{rule_loc}.response")

    def generate_provenance_report(self, csv_path: Path) -> None:
        """Check 9: Provenance coverage report."""
        if not csv_path.exists():
            self.add_error(9, "provenance.csv", "Provenance CSV file does not exist")
            return

        condition_stats: dict[str, dict[str, int]] = defaultdict(
            lambda: {"total": 0, "verified": 0}
        )
        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                cid = row.get("condition_id", "unknown")
                status = row.get("status", "unverified")
                condition_stats[cid]["total"] += 1
                if status == "verified":
                    condition_stats[cid]["verified"] += 1

        print("\n--- Provenance Coverage Report (Check 9) ---")
        for cid, stats in sorted(condition_stats.items()):
            tot = stats["total"]
            ver = stats["verified"]
            pct = (ver / tot * 100) if tot else 0.0
            print(f"  - {cid}: {ver}/{tot} verified ({pct:.1f}%)")
        print("-------------------------------------------\n")

    def write_manifest(self, manifest_path: Path) -> None:
        """Check & Part E: Write manifest.json with SHA-256 hashes."""
        file_hashes: dict[str, str] = {}
        for p in sorted(self.curated_dir.glob("*.json")):
            if p.name == "manifest.json":
                continue
            file_hashes[p.name] = compute_file_sha256(p)

        prov_path = self.curated_dir / "provenance.csv"
        if prov_path.exists():
            file_hashes["provenance.csv"] = compute_file_sha256(prov_path)

        corpus_hasher = hashlib.sha256()
        for fname, fhash in sorted(file_hashes.items()):
            corpus_hasher.update(f"{fname}:{fhash}".encode())
        overall_hash = corpus_hasher.hexdigest()

        manifest_data = {
            "version": "1.0.0",
            "overall_corpus_hash": overall_hash,
            "files": file_hashes,
        }

        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2)
            f.write("\n")
        print(f"Manifest written: {manifest_path} (Hash: {overall_hash[:12]}...)")


def main() -> None:
    """Main corpus validation entry point."""
    curated_dir = backend_root / "data" / "curated"
    lexicon_path = backend_root / "data" / "lexicon" / "drug_lexicon.txt"
    manifest_path = curated_dir / "manifest.json"
    provenance_path = curated_dir / "provenance.csv"

    validator = CorpusValidator(curated_dir, lexicon_path)

    condition_files = [
        p
        for p in sorted(curated_dir.glob("*.json"))
        if p.name not in ("urgency_rules.json", "manifest.json")
    ]
    for p in condition_files:
        validator.validate_condition_file(p)

    urgency_rules_path = curated_dir / "urgency_rules.json"
    if urgency_rules_path.exists():
        validator.validate_urgency_rules(urgency_rules_path)
    else:
        validator.add_error(1, "urgency_rules.json", "File does not exist")

    validator.generate_provenance_report(provenance_path)

    if validator.errors:
        print(f"FAILED: {len(validator.errors)} corpus validation errors detected:")
        for err in validator.errors:
            print(f"  x {err}")
        sys.exit(1)

    validator.write_manifest(manifest_path)
    print("SUCCESS: All corpus validation checks passed!")


if __name__ == "__main__":
    main()
