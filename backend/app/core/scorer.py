"""Deterministic symptom urgency scorer and clinical modifier evaluator."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.core.rule_engine import RuleEngine
from app.core.text import (
    extract_blood_pressure,
    find_phrase,
    is_negated,
    normalize,
    tokens,
)
from app.data.corpus_loader import to_corpus_condition_id, to_profile_condition_id

SEVERITY_WORDS = frozenset(
    {
        "severe",
        "unbearable",
        "worst",
        "very bad",
        "intense",
        "extreme",
        "excruciating",
        "तेज",
        "असहनीय",
        "बहुत तेज",
        "खूप जास्त",
        "असह्य",
        "तीव्र",
        "भीषण",
        "प्रचंड",
        "खूप",
        "जास्त",
        "tej",
        "tez",
        "asahniya",
        "bohot tej",
        "bohot tez",
        "bahut tej",
        "bahut tez",
        "bahut",
        "behad",
        "khoop jast",
        "khup jast",
        "khup",
        "jast",
        "asahya",
        "tivra",
        "prachand",
    }
)

CLINICAL_ESCALATORS: tuple[str, ...] = (
    "high fever",
    "fever",
    "pus",
    "blood",
    "bloody",
    "swollen glands",
    "swollen neck glands",
    "spreading",
    "persistent vomiting",
    "chest pain",
    "chest discomfort",
    "short of breath",
    "difficulty breathing",
    "confusion",
    "worsening",
    "not improving",
    "recurrent",
    "recurring",
    "repeated",
    "widespread",
    "entire",
    "all over",
    "covering",
    "sleep disturbance",
    "तेज बुखार",
    "बुखार",
    "ताप",
    "खूप ताप",
    "मवाद",
    "रक्त",
    "खून",
    "उलटी",
    "सतत उलटी",
    "सीने में दर्द",
    "छातीत दुखणे",
    "छातीत दुखत",
    "सांस लेने में तकलीफ",
    "श्वास घेण्यास त्रास",
    "tej bukhar",
    "bukhar",
    "taap",
    "khoon",
    "rakta",
    "seene mein dard",
    "chhatit dukhane",
    "saans lene mein takleef",
    "shwas ghenyas tras",
)

# Word-to-number map for duration parsing (English, Hindi, Marathi, Roman)
WORD_NUMBER_MAP: dict[str, int] = {
    "a": 1,
    "an": 1,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "few": 3,
    "couple": 2,
    "several": 4,
    "एक": 1,
    "दो": 2,
    "तीन": 3,
    "चार": 4,
    "पांच": 5,
    "पाँच": 5,
    "छह": 6,
    "सात": 7,
    "आठ": 8,
    "नौ": 9,
    "दस": 10,
    "काही": 3,
    "दोन": 2,
    "पाच": 5,
    "सहा": 6,
    "दहा": 10,
    "ek": 1,
    "do": 2,
    "don": 2,
    "teen": 3,
    "tin": 3,
    "char": 4,
    "paanch": 5,
    "panch": 5,
    "pach": 5,
    "chhah": 6,
    "chha": 6,
    "saha": 6,
    "saat": 7,
    "sat": 7,
    "aath": 8,
    "ath": 8,
    "nau": 9,
    "das": 10,
    "daha": 10,
}

DEVANAGARI_DIGITS_MAP = str.maketrans(
    {
        "०": "0",
        "१": "1",
        "२": "2",
        "३": "3",
        "४": "4",
        "५": "5",
        "६": "6",
        "७": "7",
        "८": "8",
        "९": "9",
    }
)

DURATION_PATTERNS = [
    # English prepositional
    re.compile(
        r"(?:for|since|past|lasting)\s+(\d+|[a-z\u0900-\u097f]+)\s+(days?|weeks?|months?)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(\d+|[a-z\u0900-\u097f]+)\s+(days?|weeks?|months?)\s+(?:ago|back|now|duration)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:for|since)\s+(a|an)\s+(day|week|month)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(\d+)\s+(days?|weeks?|months?)",
        re.IGNORECASE,
    ),
    # Hindi / Marathi Devanagari and Roman:
    # "3 दिन से", "तीन दिनों से", "३ दिवसांपासून", "teen din se", "3 divas"
    re.compile(
        r"(\d+|[a-z\u0900-\u097f]+)\s+(दिन|दिनों|दिवस|दिवसांपासून|हफ्ते|आठवडे|महीने|महिने)\s*(?:से|पासून)?",
        re.IGNORECASE,
    ),
    re.compile(
        r"(\d+|[a-z\u0900-\u097f]+)\s+(din|dino|divas|divasapasun|hafte|aathwade|mahine)\s*(?:se|pasun)?",
        re.IGNORECASE,
    ),
]

AGE_PATTERN = re.compile(
    r"\b(?:age\s+of\s+)?(\d{1,3})\s*(?:years?\s*old|yrs?\s*old|year\s*old|yr|yo|years|age)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ReasonHit:
    """Reason for triage rule activation."""

    rule_id: str
    kind: str
    matched_phrase: str


@dataclass(frozen=True)
class ModifierApplied:
    """Clinical modifier documentation metadata."""

    name: str
    source_id: str
    source_page: int | None = None


@dataclass
class ScoreResult:
    """Deterministic symptom urgency scoring outcome."""

    level: str  # EMERGENCY, SEE_DOCTOR, SELF_CARE, UNKNOWN
    conditions: list[str] = field(default_factory=list)
    reasons: list[dict[str, str]] = field(default_factory=list)
    modifiers_applied: list[dict[str, Any]] = field(default_factory=list)
    watch_for: list[str] = field(default_factory=list)
    urgency_note: str | None = None
    was_corrected: bool = False
    corrected_phrase: str | None = None


def extract_duration_days(text: str) -> int | None:
    """Extract symptom duration converted into total days."""
    text_clean = text.translate(DEVANAGARI_DIGITS_MAP).lower()
    for pattern in DURATION_PATTERNS:
        match = pattern.search(text_clean)
        if match:
            groups = match.groups()
            num_str = groups[0].lower()
            unit_str = groups[1].lower() if len(groups) > 1 else "days"

            num = int(num_str) if num_str.isdigit() else WORD_NUMBER_MAP.get(num_str, 1)

            if any(m in unit_str for m in ("month", "महीने", "महिने", "mahine")):
                return num * 30
            if any(w in unit_str for w in ("week", "हफ्ते", "आठवडे", "hafte", "aathwade")):
                return num * 7
            return num
    return None


def extract_patient_age(text: str) -> int | None:
    """Extract patient age in years from text if present."""
    match = AGE_PATTERN.search(text)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return None
    return None


def load_condition_profiles(lexicon_dir: Path | None = None) -> dict[str, Any]:
    """Load condition profiles from data/lexicon/condition_profiles.json."""
    if lexicon_dir is not None and lexicon_dir.is_file():
        profile_path = lexicon_dir
    else:
        base_dir = lexicon_dir or (
            Path(__file__).resolve().parent.parent.parent / "data" / "lexicon"
        )
        profile_path = base_dir / "condition_profiles.json"
    if not profile_path.exists():
        return {}
    with open(profile_path, encoding="utf-8") as f:
        profiles: dict[str, Any] = json.load(f)
    return profiles


def load_clinical_modifiers(lexicon_dir: Path | None = None) -> list[dict[str, Any]]:
    """Load clinical modifier definitions from data/lexicon/clinical_modifiers.json."""
    if lexicon_dir is not None and lexicon_dir.is_file():
        mod_path = lexicon_dir
    else:
        base_dir = lexicon_dir or (
            Path(__file__).resolve().parent.parent.parent / "data" / "lexicon"
        )
        mod_path = base_dir / "clinical_modifiers.json"
    if not mod_path.exists():
        return []
    with open(mod_path, encoding="utf-8") as f:
        modifiers: list[dict[str, Any]] = json.load(f)
    return modifiers


def _score_token_sequence(
    tok_list: list[str],
    symptoms_text: str,
    engine: RuleEngine,
    condition_profiles: dict[str, Any],
    clinical_modifiers: list[dict[str, Any]],
    watch_map: Mapping[str, list[str]],
    structured_duration: int | None = None,
    structured_modifiers: list[str] | None = None,
    forced_conditions: list[str] | None = None,
    intake_option_ids: list[str] | None = None,
) -> ScoreResult:
    """Evaluate triage urgency deterministically for a single token sequence."""
    # Extract patient age before demographic noise stripping
    extracted_age = extract_patient_age(symptoms_text)

    # Extract duration in days (use larger of text duration and structured duration)
    text_duration = extract_duration_days(symptoms_text)
    extracted_duration = max(text_duration or 0, structured_duration or 0) or None

    # Run emergency rules first. If any fires, return EMERGENCY immediately
    emergency_hits = engine.match(tok_list, kinds=["emergency"])
    active_emergency_hits = [h for h in emergency_hits if not h.skipped_by_negation]
    if active_emergency_hits:
        first_emerg = active_emergency_hits[0]
        reasons = [
            {
                "rule_id": h.rule_id,
                "kind": h.kind,
                "matched_phrase": h.matched_phrase,
            }
            for h in active_emergency_hits
        ]
        return ScoreResult(
            level="EMERGENCY",
            conditions=[first_emerg.condition] if first_emerg.condition else [],
            reasons=reasons,
            urgency_note=first_emerg.response,
        )

    # 3. Detect conditions with aliases in condition profiles (negation-aware whole-token matching)
    detected_conditions: list[str] = []
    for cond_id, profile in condition_profiles.items():
        aliases: list[str] = profile.get("aliases", [])
        matched = False
        for alias in aliases:
            alias_toks = alias.strip().lower().split()
            if not alias_toks:
                continue
            matches = find_phrase(tok_list, alias_toks)
            if matches and any(not is_negated(tok_list, m, len(alias_toks)) for m in matches):
                matched = True
                break
        if matched:
            detected_conditions.append(cond_id)

    # 3b. If no conditions detected from text, use forced_conditions from intake area answer
    if not detected_conditions and forced_conditions:
        for fc in forced_conditions:
            if fc in condition_profiles and fc not in detected_conditions:
                detected_conditions.append(fc)

    # 4. Run see_doctor and self_care rules from engine
    other_hits = engine.match(tok_list, kinds=["see_doctor", "self_care"])
    active_other_hits = [h for h in other_hits if not h.skipped_by_negation]

    # Register condition from rule hit if present
    for h in active_other_hits:
        if h.source_id:
            prof_cid = to_profile_condition_id(h.source_id)
            if prof_cid in condition_profiles and prof_cid not in detected_conditions:
                detected_conditions.append(prof_cid)

    # 5. Start from highest level reached by any matched rule or floor level
    level = "UNKNOWN"
    reasons_list: list[dict[str, str]] = []
    urgency_note: str | None = None

    see_doc_hits = [h for h in active_other_hits if h.kind == "see_doctor"]
    self_care_hits = [h for h in active_other_hits if h.kind == "self_care"]

    if see_doc_hits:
        level = "SEE_DOCTOR"
        urgency_note = see_doc_hits[0].response
        for h in see_doc_hits:
            reasons_list.append(
                {
                    "rule_id": h.rule_id,
                    "kind": h.kind,
                    "matched_phrase": h.matched_phrase,
                }
            )
    elif self_care_hits:
        level = "SELF_CARE"
        urgency_note = self_care_hits[0].response
        for h in self_care_hits:
            reasons_list.append(
                {
                    "rule_id": h.rule_id,
                    "kind": h.kind,
                    "matched_phrase": h.matched_phrase,
                }
            )
    elif detected_conditions:
        # Check floor levels of detected conditions
        has_see_doctor_floor = any(
            condition_profiles.get(cid, {}).get("floor_level") == "SEE_DOCTOR"
            for cid in detected_conditions
        )
        if has_see_doctor_floor:
            level = "SEE_DOCTOR"
            reasons_list.append(
                {
                    "rule_id": "CONDITION_FLOOR_LEVEL",
                    "kind": "floor_level",
                    "matched_phrase": ", ".join(detected_conditions),
                }
            )
        else:
            level = "SELF_CARE"
            reasons_list.append(
                {
                    "rule_id": "CONDITION_FLOOR_LEVEL",
                    "kind": "floor_level",
                    "matched_phrase": ", ".join(detected_conditions),
                }
            )

    # 5b. Evaluate numeric blood pressure readings (e.g. 148/94)
    bp = extract_blood_pressure(symptoms_text)
    if bp:
        systolic, diastolic = bp
        if systolic >= 140 or diastolic >= 90:
            if "hypertension" not in detected_conditions:
                detected_conditions.append("hypertension")
            if level == "SELF_CARE" or level == "UNKNOWN":
                level = "SEE_DOCTOR"
            reasons_list.append(
                {
                    "rule_id": "BP_THRESHOLD_ELEVATED",
                    "kind": "blood_pressure",
                    "matched_phrase": f"{systolic}/{diastolic}",
                }
            )

    # 5c. Headache with elevated BP comorbidity
    if "headache" in detected_conditions:
        has_high_bp_text = any(
            find_phrase(tok_list, p.split())
            and any(
                not is_negated(tok_list, m, len(p.split()))
                for m in find_phrase(tok_list, p.split())
            )
            for p in (
                "high bp",
                "elevated bp",
                "elevated blood pressure",
                "high blood pressure",
                "hypertension",
            )
        )
        if has_high_bp_text or "hypertension" in detected_conditions:
            if level == "SELF_CARE" or level == "UNKNOWN":
                level = "SEE_DOCTOR"
            reasons_list.append(
                {
                    "rule_id": "HEADACHE_WITH_HIGH_BP",
                    "kind": "comorbidity",
                    "matched_phrase": "headache with elevated blood pressure",
                }
            )

    # 6. Severity words raise SELF_CARE to SEE_DOCTOR
    for word in SEVERITY_WORDS:
        word_toks = word.split()
        matches = find_phrase(tok_list, word_toks)
        if matches and any(not is_negated(tok_list, m, len(word_toks)) for m in matches):
            if level == "SELF_CARE":
                level = "SEE_DOCTOR"
                reasons_list.append(
                    {
                        "rule_id": "SEVERITY_ESCALATION",
                        "kind": "severity",
                        "matched_phrase": word,
                    }
                )
            break

    # 6b. Clinical escalators (raise SELF_CARE floor conditions to SEE_DOCTOR)
    if level == "SELF_CARE" and detected_conditions:
        for esc in CLINICAL_ESCALATORS:
            if esc in ("blood", "bloody") and detected_conditions == ["epistaxis_nosebleed"]:
                continue
            esc_toks = esc.split()
            matches = find_phrase(tok_list, esc_toks)
            if matches and any(not is_negated(tok_list, m, len(esc_toks)) for m in matches):
                level = "SEE_DOCTOR"
                reasons_list.append(
                    {
                        "rule_id": "CLINICAL_ESCALATOR",
                        "kind": "escalator",
                        "matched_phrase": esc,
                    }
                )
                break

    # 7. Duration threshold escalation
    if extracted_duration is not None and detected_conditions:
        for cid in detected_conditions:
            profile = condition_profiles.get(cid, {})
            duration_rules = profile.get("duration_rules", [])
            for drule in duration_rules:
                thresh = drule.get("threshold_days", 999)
                if extracted_duration >= thresh:
                    target_lvl = drule.get("escalate_to", "SEE_DOCTOR")
                    if level == "SELF_CARE" or level == "UNKNOWN":
                        level = target_lvl
                        reasons_list.append(
                            {
                                "rule_id": f"DURATION_THRESHOLD_{cid.upper()}",
                                "kind": "duration",
                                "matched_phrase": (
                                    f"{extracted_duration} days (threshold {thresh} days)"
                                ),
                            }
                        )

    # 8. Clinical modifiers (can only raise to at least SEE_DOCTOR)
    modifiers_applied: list[dict[str, Any]] = []
    for mod in clinical_modifiers:
        mod_id = mod.get("id", "")
        trigger_terms = mod.get("trigger_terms", [])
        min_age = mod.get("min_age")
        target_conditions = mod.get("target_conditions", [])

        # Check term match
        term_matched = False
        matched_term = ""
        for term in trigger_terms:
            t_toks = term.strip().lower().split()
            if not t_toks:
                continue
            matches = find_phrase(tok_list, t_toks)
            if matches and any(not is_negated(tok_list, m, len(t_toks)) for m in matches):
                term_matched = True
                matched_term = term
                break

        # Check age criteria for elderly modifier
        age_matched = False
        if min_age is not None and extracted_age is not None and extracted_age >= min_age:
            age_matched = True

        # Check structured modifiers from intake answers
        struct_matched = False
        if structured_modifiers:
            for sm in structured_modifiers:
                sm_clean = sm.strip().lower()
                if (
                    sm_clean in mod_id.lower()
                    or sm_clean == mod.get("name", "").lower()
                    or (sm_clean == "pregnancy" and "pregnancy" in mod_id.lower())
                    or (sm_clean == "diabetes" and "diabetes" in mod_id.lower())
                    or (sm_clean == "immunocompromised" and "immunocompromised" in mod_id.lower())
                    or (sm_clean == "elderly" and "elderly" in mod_id.lower())
                ):
                    struct_matched = True
                    matched_term = sm_clean
                    break

        if term_matched or age_matched or struct_matched:
            # Check which detected conditions match the modifier pairs
            pairs_list = mod.get("pairs", [])
            matching_pairs = [p for p in pairs_list if p.get("condition_id") in detected_conditions]
            if (
                not matching_pairs
                and not pairs_list
                and (
                    any(c in target_conditions for c in detected_conditions)
                    or not target_conditions
                )
            ):
                fallback_cid = detected_conditions[0] if detected_conditions else "unknown"
                matching_pairs = [
                    {
                        "condition_id": fallback_cid,
                        "source_id": mod.get("source_id", "clinical-guidelines"),
                        "source_page": mod.get("source_page", 1),
                    }
                ]

            if matching_pairs:
                if level == "SELF_CARE" or level == "UNKNOWN":
                    level = mod.get("escalate_to", "SEE_DOCTOR")
                for p in matching_pairs:
                    modifiers_applied.append(
                        {
                            "name": mod.get("name", mod_id),
                            "condition_id": p.get("condition_id", ""),
                            "source_id": p.get("source_id", "clinical-guidelines"),
                            "source_page": p.get("source_page", 1),
                            "quote": p.get("quote", ""),
                        }
                    )
                phrase_detail = matched_term or (f"age {extracted_age}" if age_matched else "")
                reasons_list.append(
                    {
                        "rule_id": mod_id,
                        "kind": "clinical_modifier",
                        "matched_phrase": phrase_detail,
                    }
                )

    # 9. If nothing detected and no rule matched, return UNKNOWN
    if level == "UNKNOWN" and not detected_conditions and not reasons_list:
        return ScoreResult(level="UNKNOWN")

    # If conditions detected but level still UNKNOWN, default to SEE_DOCTOR or SELF_CARE
    if level == "UNKNOWN" and detected_conditions:
        level = "SELF_CARE"

    # 10. Gather watch_for items up to 5 plain strings
    watch_for_items: list[str] = []
    for cid in detected_conditions:
        items = watch_map.get(cid, []) or watch_map.get(to_corpus_condition_id(cid), [])
        for it in items:
            if it not in watch_for_items:
                watch_for_items.append(it)
            if len(watch_for_items) >= 5:
                break
        if len(watch_for_items) >= 5:
            break

    return ScoreResult(
        level=level,
        conditions=detected_conditions,
        reasons=reasons_list,
        modifiers_applied=modifiers_applied,
        watch_for=watch_for_items,
        urgency_note=urgency_note,
    )


def symptom_urgency_scorer(
    symptoms: str,
    engine: RuleEngine,
    profiles: dict[str, Any] | None = None,
    watch_for: Mapping[str, list[str]] | None = None,
    modifiers_def: list[dict[str, Any]] | None = None,
    structured_duration: int | None = None,
    structured_modifiers: list[str] | None = None,
    forced_conditions: list[str] | None = None,
    intake_option_ids: list[str] | None = None,
) -> ScoreResult:
    """Score symptom urgency deterministically based only on rule tables and clinical guidelines.

    Evaluates original tokens first, then candidate sequences from spelling correction in an
    escalate-only manner. Never lowers urgency.
    """
    if not symptoms or not symptoms.strip():
        return ScoreResult(level="UNKNOWN")

    condition_profiles = profiles if profiles is not None else load_condition_profiles()
    clinical_modifiers = modifiers_def if modifiers_def is not None else load_clinical_modifiers()
    watch_map = watch_for or {}

    norm_text = normalize(symptoms)
    tok_list = tokens(norm_text)

    # 1. Base evaluation on uncorrected tokens
    base_res = _score_token_sequence(
        tok_list=tok_list,
        symptoms_text=symptoms,
        engine=engine,
        condition_profiles=condition_profiles,
        clinical_modifiers=clinical_modifiers,
        watch_map=watch_map,
        structured_duration=structured_duration,
        structured_modifiers=structured_modifiers,
        forced_conditions=forced_conditions,
        intake_option_ids=intake_option_ids,
    )

    # If already an emergency on base text, no correction needed
    if base_res.level == "EMERGENCY":
        return base_res

    # 2. Check candidate sequences for misspelled words (escalate-only)
    from app.core.spelling import get_spelling_corrector

    spelling = get_spelling_corrector()
    candidate_seqs = spelling.get_candidate_sequences(tok_list)

    if len(candidate_seqs) > 1:
        severity_order: dict[str, int] = {
            "UNKNOWN": 0,
            "SELF_CARE": 1,
            "SEE_DOCTOR": 2,
            "EMERGENCY": 3,
        }
        for cand_toks, _was_corr, phrase_desc in candidate_seqs[1:]:
            cand_text = " ".join(cand_toks)
            cand_res = _score_token_sequence(
                tok_list=cand_toks,
                symptoms_text=cand_text,
                engine=engine,
                condition_profiles=condition_profiles,
                clinical_modifiers=clinical_modifiers,
                watch_map=watch_map,
                structured_duration=structured_duration,
                structured_modifiers=structured_modifiers,
                forced_conditions=forced_conditions,
                intake_option_ids=intake_option_ids,
            )
            cand_rank = severity_order.get(cand_res.level, 0)
            base_rank = severity_order.get(base_res.level, 0)

            if (cand_rank > base_rank) or (
                cand_rank == base_rank and cand_res.conditions and not base_res.conditions
            ):
                cand_res.was_corrected = True
                cand_res.corrected_phrase = phrase_desc or (" ".join(cand_toks))
                base_res = cand_res

            if base_res.level == "EMERGENCY":
                break

    return base_res
