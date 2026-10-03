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

SEVERITY_WORDS = frozenset(
    {
        "severe",
        "unbearable",
        "worst",
        "very bad",
        "intense",
        "extreme",
        "excruciating",
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
)

# Word-to-number map for duration parsing
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
}

DURATION_PATTERNS = [
    re.compile(
        r"(?:for|since|past|lasting)\s+(\d+|one|two|three|four|five|six|seven|eight|nine|ten|few|couple|several)\s+(days?|weeks?|months?)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(\d+|one|two|three|four|five|six|seven|eight|nine|ten|few|couple|several)\s+(days?|weeks?|months?)\s+(?:ago|back|now|duration)",
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


def extract_duration_days(text: str) -> int | None:
    """Extract symptom duration converted into total days."""
    text_lower = text.lower()
    for pattern in DURATION_PATTERNS:
        match = pattern.search(text_lower)
        if match:
            groups = match.groups()
            num_str = groups[0].lower()
            unit_str = groups[1].lower() if len(groups) > 1 else "days"

            num = int(num_str) if num_str.isdigit() else WORD_NUMBER_MAP.get(num_str, 1)

            if "month" in unit_str:
                return num * 30
            if "week" in unit_str:
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


def symptom_urgency_scorer(
    symptoms: str,
    engine: RuleEngine,
    profiles: dict[str, Any] | None = None,
    watch_for: Mapping[str, list[str]] | None = None,
    modifiers_def: list[dict[str, Any]] | None = None,
) -> ScoreResult:
    """Score symptom urgency deterministically based only on rule tables and clinical guidelines.

    Never calls an external model or network.
    """
    if not symptoms or not symptoms.strip():
        return ScoreResult(level="UNKNOWN")

    # Load defaults if omitted
    condition_profiles = profiles if profiles is not None else load_condition_profiles()
    clinical_modifiers = modifiers_def if modifiers_def is not None else load_clinical_modifiers()
    watch_map = watch_for or {}

    # Extract patient age before demographic noise stripping
    extracted_age = extract_patient_age(symptoms)

    # Extract duration in days
    extracted_duration = extract_duration_days(symptoms)

    # 1. Normalize and tokenize text
    norm_text = normalize(symptoms)
    tok_list = tokens(norm_text)

    # 2. Run emergency rules first. If any fires, return EMERGENCY immediately
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
            if matches and any(not is_negated(tok_list, m) for m in matches):
                matched = True
                break
        if matched:
            detected_conditions.append(cond_id)

    # 4. Run see_doctor and self_care rules from engine
    other_hits = engine.match(tok_list, kinds=["see_doctor", "self_care"])
    active_other_hits = [h for h in other_hits if not h.skipped_by_negation]

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
    bp = extract_blood_pressure(symptoms)
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
            and any(not is_negated(tok_list, m) for m in find_phrase(tok_list, p.split()))
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
        if matches and any(not is_negated(tok_list, m) for m in matches):
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
            if matches and any(not is_negated(tok_list, m) for m in matches):
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
        target_symptoms = mod.get("target_symptoms", [])

        # Check term match
        term_matched = False
        matched_term = ""
        for term in trigger_terms:
            t_toks = term.strip().lower().split()
            if not t_toks:
                continue
            matches = find_phrase(tok_list, t_toks)
            if matches and any(not is_negated(tok_list, m) for m in matches):
                term_matched = True
                matched_term = term
                break

        # Check age criteria for elderly modifier
        age_matched = False
        if min_age is not None and extracted_age is not None and extracted_age >= min_age:
            age_matched = True

        if term_matched or age_matched:
            # Check if target conditions or symptom terms are present
            condition_relevant = any(c in target_conditions for c in detected_conditions)
            symptom_relevant = False
            if not condition_relevant:
                for symp in target_symptoms:
                    s_toks = symp.strip().lower().split()
                    matches = find_phrase(tok_list, s_toks)
                    if matches and any(not is_negated(tok_list, m) for m in matches):
                        symptom_relevant = True
                        break

            if condition_relevant or symptom_relevant or not target_conditions:
                if level == "SELF_CARE" or level == "UNKNOWN":
                    level = mod.get("escalate_to", "SEE_DOCTOR")
                modifiers_applied.append(
                    {
                        "name": mod.get("name", mod_id),
                        "source_id": mod.get("source_id", "clinical-guidelines"),
                        "source_page": mod.get("source_page", 1),
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
        items = watch_map.get(cid, [])
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
