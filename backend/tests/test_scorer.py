"""Unit tests for symptom_urgency_scorer, duration parsing, and clinical modifiers."""

from typing import Any

import pytest

from app.core.rule_engine import RuleEngine
from app.core.scorer import (
    extract_duration_days,
    extract_patient_age,
    load_clinical_modifiers,
    load_condition_profiles,
    symptom_urgency_scorer,
)
from app.data.rules_loader import load_drug_lexicon_list, load_raw_rules


@pytest.fixture(scope="module")
def rule_engine() -> RuleEngine:
    """Instantiate a production RuleEngine with v2 urgency rules."""
    rules = load_raw_rules()
    drugs = load_drug_lexicon_list()
    return RuleEngine(rules=rules, lexicon=drugs)


@pytest.fixture(scope="module")
def profiles() -> dict[str, Any]:
    """Load condition profiles dictionary."""
    return load_condition_profiles()


@pytest.fixture(scope="module")
def modifiers() -> list[dict[str, Any]]:
    """Load clinical modifiers list."""
    return load_clinical_modifiers()


@pytest.fixture(scope="module")
def watch_for_map() -> dict[str, list[str]]:
    """Sample danger signs / watch_for mapping by condition id."""
    return {
        "headache": [
            "Sudden explosive thunderclap headache",
            "Headache with stiff neck and fever",
        ],
        "acute_respiratory_infections": [
            "Difficulty breathing or blue lips",
            "Stridor",
        ],
        "urinary_tract_infection": [
            "High fever with shaking chills",
            "Severe flank pain",
        ],
        "acute_diarrhea": [
            "Unable to drink fluids",
            "Lethargy or loss of consciousness",
        ],
    }


# ---------------------------------------------------------------------------
# 1. Duration and Age Extraction Tests
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("text", "expected_days"),
    [
        ("I have headache for 3 days", 3),
        ("cough lasting 2 weeks", 14),
        ("sinus pain for a month", 30),
        ("diarrhea since 5 days now", 5),
        ("sore throat for one week", 7),
        ("pain for several days", 4),
        ("loose motions for a day", 1),
    ],
)
def test_extract_duration_days(text: str, expected_days: int) -> None:
    """Durations in various text formats are accurately converted to days."""
    assert extract_duration_days(text) == expected_days


@pytest.mark.parametrize(
    ("text", "expected_age"),
    [
        ("I am 68 years old and have a cough", 68),
        ("Patient age of 75 years with fever", 75),
        ("82 yo grandmother with cold", 82),
        ("24 yr old man with headache", 24),
    ],
)
def test_extract_patient_age(text: str, expected_age: int) -> None:
    """Patient age is correctly extracted across phrasing formats."""
    assert extract_patient_age(text) == expected_age


# ---------------------------------------------------------------------------
# 2. Precedence and Emergency Override
# ---------------------------------------------------------------------------
def test_emergency_takes_precedence_in_scorer(
    rule_engine: RuleEngine,
    profiles: dict[str, Any],
    watch_for_map: dict[str, list[str]],
) -> None:
    """Emergency symptoms must immediately return EMERGENCY."""
    res = symptom_urgency_scorer(
        "I have severe crushing chest pain radiating to left arm",
        engine=rule_engine,
        profiles=profiles,
        watch_for=watch_for_map,
    )
    assert res.level == "EMERGENCY"
    assert any("ER-" in r["rule_id"] for r in res.reasons)


# ---------------------------------------------------------------------------
# 3. Floor Levels and Condition Detection
# ---------------------------------------------------------------------------
def test_mild_headache_self_care_floor(
    rule_engine: RuleEngine,
    profiles: dict[str, Any],
    watch_for_map: dict[str, list[str]],
) -> None:
    """Mild headache without red flags evaluates to SELF_CARE."""
    res = symptom_urgency_scorer(
        "I have a mild headache for 2 days",
        engine=rule_engine,
        profiles=profiles,
        watch_for=watch_for_map,
    )
    assert res.level == "SELF_CARE"
    assert "headache" in res.conditions
    assert len(res.watch_for) > 0


def test_uti_see_doctor_floor(
    rule_engine: RuleEngine,
    profiles: dict[str, Any],
    watch_for_map: dict[str, list[str]],
) -> None:
    """UTI symptoms evaluate to SEE_DOCTOR because UTI floor level requires prescription."""
    res = symptom_urgency_scorer(
        "I have burning when passing urine for 1 day",
        engine=rule_engine,
        profiles=profiles,
        watch_for=watch_for_map,
    )
    assert res.level == "SEE_DOCTOR"
    assert "urinary_tract_infection" in res.conditions


# ---------------------------------------------------------------------------
# 4. Severity Escalation
# ---------------------------------------------------------------------------
def test_severity_word_escalation(
    rule_engine: RuleEngine,
    profiles: dict[str, Any],
    watch_for_map: dict[str, list[str]],
) -> None:
    """Words like severe or unbearable raise SELF_CARE to SEE_DOCTOR."""
    res = symptom_urgency_scorer(
        "I have severe throat pain for 1 day",
        engine=rule_engine,
        profiles=profiles,
        watch_for=watch_for_map,
    )
    assert res.level == "SEE_DOCTOR"
    assert any(r["kind"] == "severity" for r in res.reasons)


# ---------------------------------------------------------------------------
# 5. Duration Threshold Escalation
# ---------------------------------------------------------------------------
def test_duration_threshold_escalation(
    rule_engine: RuleEngine,
    profiles: dict[str, Any],
    watch_for_map: dict[str, list[str]],
) -> None:
    """Headache lasting 7 days or more escalates from SELF_CARE to SEE_DOCTOR."""
    # Under threshold -> SELF_CARE
    res_mild = symptom_urgency_scorer(
        "I have mild headache for 4 days",
        engine=rule_engine,
        profiles=profiles,
        watch_for=watch_for_map,
    )
    assert res_mild.level == "SELF_CARE"

    # At or above threshold -> SEE_DOCTOR
    res_long = symptom_urgency_scorer(
        "I have mild headache for 8 days",
        engine=rule_engine,
        profiles=profiles,
        watch_for=watch_for_map,
    )
    assert res_long.level == "SEE_DOCTOR"
    assert any("DURATION" in r["rule_id"] for r in res_long.reasons)


# ---------------------------------------------------------------------------
# 6. Clinical Modifiers
# ---------------------------------------------------------------------------
def test_pregnancy_clinical_modifier(
    rule_engine: RuleEngine,
    profiles: dict[str, Any],
    watch_for_map: dict[str, list[str]],
) -> None:
    """Pregnancy raises headache or fever to at least SEE_DOCTOR."""
    res = symptom_urgency_scorer(
        "I am pregnant and have a mild headache for 1 day",
        engine=rule_engine,
        profiles=profiles,
        watch_for=watch_for_map,
    )
    assert res.level == "SEE_DOCTOR"
    assert any(m["name"] == "Pregnancy Clinical Modifier" for m in res.modifiers_applied)


def test_diabetes_infection_modifier(
    rule_engine: RuleEngine,
    profiles: dict[str, Any],
    watch_for_map: dict[str, list[str]],
) -> None:
    """Diabetes raises infections or boils to at least SEE_DOCTOR."""
    res = symptom_urgency_scorer(
        "I am a diabetic patient with a small boil on my skin",
        engine=rule_engine,
        profiles=profiles,
        watch_for=watch_for_map,
    )
    assert res.level == "SEE_DOCTOR"
    assert any(m["name"] == "Diabetes Infection Modifier" for m in res.modifiers_applied)


def test_elderly_respiratory_modifier(
    rule_engine: RuleEngine,
    profiles: dict[str, Any],
    watch_for_map: dict[str, list[str]],
) -> None:
    """Age 65 or above raises acute respiratory symptoms to SEE_DOCTOR."""
    res = symptom_urgency_scorer(
        "I am 72 years old with a mild cold and runny nose for 2 days",
        engine=rule_engine,
        profiles=profiles,
        watch_for=watch_for_map,
    )
    assert res.level == "SEE_DOCTOR"
    assert any(m["name"] == "Elderly High-Risk Group Modifier" for m in res.modifiers_applied)


# ---------------------------------------------------------------------------
# 7. Demographic Invariance (Non-clinical modifiers do not change result)
# ---------------------------------------------------------------------------
def test_non_clinical_demographic_invariance(
    rule_engine: RuleEngine,
    profiles: dict[str, Any],
    watch_for_map: dict[str, list[str]],
) -> None:
    """Demographics like young adult age, occupation, or gender do not alter triage."""
    base_res = symptom_urgency_scorer(
        "mild headache for 2 days",
        engine=rule_engine,
        profiles=profiles,
        watch_for=watch_for_map,
    )
    preambled_res = symptom_urgency_scorer(
        "I am a 28 years old male farmer with mild headache for 2 days",
        engine=rule_engine,
        profiles=profiles,
        watch_for=watch_for_map,
    )
    assert base_res.level == preambled_res.level == "SELF_CARE"


# ---------------------------------------------------------------------------
# 8. Negation and UNKNOWN Fallback
# ---------------------------------------------------------------------------
def test_negation_suppresses_condition(
    rule_engine: RuleEngine,
    profiles: dict[str, Any],
    watch_for_map: dict[str, list[str]],
) -> None:
    """Negated conditions are not registered as active detected conditions."""
    res = symptom_urgency_scorer(
        "I have no headache but mild runny nose for 2 days",
        engine=rule_engine,
        profiles=profiles,
        watch_for=watch_for_map,
    )
    assert "headache" not in res.conditions
    assert "acute_respiratory_infections" in res.conditions
    assert res.level == "SELF_CARE"


def test_unknown_query_returns_unknown(
    rule_engine: RuleEngine,
    profiles: dict[str, Any],
    watch_for_map: dict[str, list[str]],
) -> None:
    """Queries unrelated to medical symptoms return UNKNOWN level."""
    res = symptom_urgency_scorer(
        "What is the weather in Delhi today?",
        engine=rule_engine,
        profiles=profiles,
        watch_for=watch_for_map,
    )
    assert res.level == "UNKNOWN"
    assert len(res.conditions) == 0
