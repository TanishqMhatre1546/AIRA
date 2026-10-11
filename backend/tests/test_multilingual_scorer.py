"""Unit tests for multilingual symptom urgency scoring in Hindi and Marathi."""

from typing import Any

import pytest

from app.core.rule_engine import RuleEngine
from app.core.scorer import (
    extract_duration_days,
    load_clinical_modifiers,
    load_condition_profiles,
    symptom_urgency_scorer,
)
from app.data.rules_loader import load_drug_lexicon_list, load_raw_rules


@pytest.fixture(scope="module")
def rule_engine() -> RuleEngine:
    """Instantiate a production RuleEngine with urgency rules."""
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
    """Danger signs watch_for mapping by condition id."""
    return {
        "headache": ["Sudden thunderclap headache", "Stiff neck and fever"],
        "acute_respiratory_infections": ["Difficulty breathing or blue lips", "Stridor"],
        "urinary_tract_infection": ["High fever with shaking chills", "Severe flank pain"],
        "acute_diarrhea": ["Unable to drink fluids", "Lethargy or loss of consciousness"],
    }


# ---------------------------------------------------------------------------
# Test 1: Duration extraction with Devanagari and Roman Hindi/Marathi
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "text, expected_days",
    [
        ("मला ३ दिवसांपासून ताप आहे", 3),
        ("खोकला १० दिवस चालू आहे", 10),
        ("सिरदर्द 5 दिन से हो रहा है", 5),
        ("२ आठवडे जुलाब होत आहेत", 14),
        ("तीन दिनों से बुखार है", 3),
        ("teen din se sirdard hai", 3),
        ("5 divas pasun khokla ahe", 5),
        ("1 mahine se ulti ho rahi hai", 30),
    ],
)
def test_multilingual_duration_extraction(text: str, expected_days: int) -> None:
    """Extract durations correctly from Indic scripts, digits, and units."""
    days = extract_duration_days(text)
    assert days == expected_days


# ---------------------------------------------------------------------------
# Test 2: Condition alias detection across Hindi and Marathi
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "query, expected_condition",
    [
        # Hindi Devanagari
        ("मुझे सिरदर्द है और हल्का बुखार", "headache"),
        ("सर्दी और जुकाम हो गया है", "acute_respiratory_infections"),
        ("उल्टी और दस्त लग गए हैं", "acute_diarrhea"),
        ("पेशाब में जलन हो रही है", "urinary_tract_infection"),
        ("त्वचा पर दाद और खुजली है", "dermatophytosis"),
        # Hindi Roman
        ("bohot tez sirdard ho raha hai", "headache"),
        ("sardi khasi aur zukam hai", "acute_respiratory_infections"),
        ("dast aur ulti lag gayi hai", "acute_diarrhea"),
        ("peshab me jalan ho rahi hai", "urinary_tract_infection"),
        # Marathi Devanagari
        ("मला डोकेदुखीचा त्रास होतोय", "headache"),
        ("खोकला आणि सर्दी झाली आहे", "acute_respiratory_infections"),
        ("पातळ संडास आणि पोटदुखी", "acute_diarrhea"),
        ("लघवी करताना जळजळ होते", "urinary_tract_infection"),
        ("अंगावर खाज आणि पुरळ", "scabies"),
        # Marathi Roman
        ("khup dokedukhi hotiye", "headache"),
        ("khokla aani sardi zali ahe", "acute_respiratory_infections"),
        ("patal sandas aani ulti", "acute_diarrhea"),
        ("laghvi kartanna jaljal hot ahe", "urinary_tract_infection"),
    ],
)
def test_multilingual_condition_alias_detection(
    rule_engine: RuleEngine,
    profiles: dict[str, Any],
    watch_for_map: dict[str, list[str]],
    modifiers: list[dict[str, Any]],
    query: str,
    expected_condition: str,
) -> None:
    """Multilingual aliases correctly map user phrasing to condition IDs."""
    res = symptom_urgency_scorer(
        symptoms=query,
        engine=rule_engine,
        profiles=profiles,
        watch_for=watch_for_map,
        modifiers_def=modifiers,
    )
    assert expected_condition in res.conditions


# ---------------------------------------------------------------------------
# Test 3: Duration-based escalation to SEE_DOCTOR
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "query",
    [
        "सिरदर्द १० दिन से लगातार हो रहा है",
        "dokedukhi 15 divas chaloo ahe",
        "खोकला ४ आठवडे चालू आहे",
        "patal sandas 10 din se ho raha hai",
    ],
)
def test_multilingual_duration_escalation(
    rule_engine: RuleEngine,
    profiles: dict[str, Any],
    watch_for_map: dict[str, list[str]],
    modifiers: list[dict[str, Any]],
    query: str,
) -> None:
    """Indic symptoms lasting beyond thresholds escalate to SEE_DOCTOR."""
    res = symptom_urgency_scorer(
        symptoms=query,
        engine=rule_engine,
        profiles=profiles,
        watch_for=watch_for_map,
        modifiers_def=modifiers,
    )
    assert res.level == "SEE_DOCTOR"
    assert any(
        "duration" in r["rule_id"].lower() or "modifier" in r["rule_id"].lower()
        for r in res.reasons
    )


# ---------------------------------------------------------------------------
# Test 4: Severity-based escalation to SEE_DOCTOR
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "query",
    [
        "खूप जास्त डोकेदुखी होत आहे",
        "bahut tez sirdard hai",
        "प्रचंड खोकला आणि कफ",
    ],
)
def test_multilingual_severity_escalation(
    rule_engine: RuleEngine,
    profiles: dict[str, Any],
    watch_for_map: dict[str, list[str]],
    modifiers: list[dict[str, Any]],
    query: str,
) -> None:
    """Indic high-severity symptoms escalate to SEE_DOCTOR."""
    res = symptom_urgency_scorer(
        symptoms=query,
        engine=rule_engine,
        profiles=profiles,
        watch_for=watch_for_map,
        modifiers_def=modifiers,
    )
    assert res.level in ("SEE_DOCTOR", "EMERGENCY")


# ---------------------------------------------------------------------------
# Test 5: Scorer emergency escalation
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "query",
    [
        "मला छातीत तीव्र वेदना होत आहेत आणि घाम येतोय",
        "seene mein behad tez dard ho raha hai",
    ],
)
def test_multilingual_scorer_emergency(
    rule_engine: RuleEngine,
    profiles: dict[str, Any],
    watch_for_map: dict[str, list[str]],
    modifiers: list[dict[str, Any]],
    query: str,
) -> None:
    """Urgent indicators in scorer input escalate to EMERGENCY."""
    res = symptom_urgency_scorer(
        symptoms=query,
        engine=rule_engine,
        profiles=profiles,
        watch_for=watch_for_map,
        modifiers_def=modifiers,
    )
    assert res.level == "EMERGENCY"


# ---------------------------------------------------------------------------
# Test 6: Benign / Self Care queries
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "query",
    [
        "हल्का सिरदर्द १ दिन से",
        "halka sirdard 1 din se",
        "हल्की सर्दी १ दिवस",
        "halki sardi 1 divas",
    ],
)
def test_multilingual_self_care(
    rule_engine: RuleEngine,
    profiles: dict[str, Any],
    watch_for_map: dict[str, list[str]],
    modifiers: list[dict[str, Any]],
    query: str,
) -> None:
    """Mild Indic symptoms of 1 day duration route to SELF_CARE."""
    res = symptom_urgency_scorer(
        symptoms=query,
        engine=rule_engine,
        profiles=profiles,
        watch_for=watch_for_map,
        modifiers_def=modifiers,
    )
    assert res.level == "SELF_CARE"


# ---------------------------------------------------------------------------
# Test 7: Succeeding Negation in Indic scorer queries
# ---------------------------------------------------------------------------
def test_multilingual_scorer_succeeding_negation(
    rule_engine: RuleEngine,
    profiles: dict[str, Any],
    watch_for_map: dict[str, list[str]],
    modifiers: list[dict[str, Any]],
) -> None:
    """Post-phrase negation in Hindi/Marathi prevents false emergency escalations."""
    # Negated emergency: 'khokla ahe pan chhatit dukhat nahi' (Cough is there, but no chest pain)
    res = symptom_urgency_scorer(
        symptoms="खोकला आहे पण छातीत दुखत नाही १ दिवस",
        engine=rule_engine,
        profiles=profiles,
        watch_for=watch_for_map,
        modifiers_def=modifiers,
    )
    assert res.level != "EMERGENCY"
    assert "acute_respiratory_infections" in res.conditions
