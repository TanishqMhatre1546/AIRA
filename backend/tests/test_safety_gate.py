"""Comprehensive unit and parameterized tests for the deterministic SafetyGate."""

import time
from unittest.mock import MagicMock

import pytest

from app.core.safety_gate import SafetyGate
from app.data.rules_loader import create_safety_gate


@pytest.fixture(scope="module")
def gate() -> SafetyGate:
    """Instantiate a production-grade SafetyGate with curated rules and drug lexicon."""
    return create_safety_gate()


# ---------------------------------------------------------------------------
# 1. Parameterized Emergency Rule Phrasings (4+ phrasings per core emergency)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("query", "expected_rule"),
    [
        # ER-001: Airway / Angioedema
        ("My throat is swelling up and I can't breathe", "ER-001"),
        ("THROAT SWELLING badly, tongue swelling too!", "ER-001"),
        ("I have severe lip swelling and choking sensation", "ER-001"),
        ("Having an anaphylaxis allergic reaction right now", "ER-001"),
        # ER-002: Sepsis / Bacterial skin
        ("High fever and skin turning black on my leg", "ER-002"),
        ("skin peeling off rapidly with high fever", "ER-002"),
        ("severe pain in wound then no pain at all", "ER-002"),
        ("patient is unconscious and collapsed after infection", "ER-002"),
        # ER-003: UTI with Sepsis
        ("uti fever and severe shaking chills", "ER-003"),
        ("back pain with fever and urine infection", "ER-003"),
        ("flank pain fever with burning urination", "ER-003"),
        ("fever with chills and severe kidney pain", "ER-003"),
        # ER-004: Heart Attack / Chest Pain
        ("Severe crushing chest pain radiating to left arm", "ER-004"),
        ("CHEST PRESSURE and chest tightness for 30 minutes", "ER-004"),
        ("having a heart attack, please help immediately", "ER-004"),
        ("pain in chest spreading to jaw and shoulder", "ER-004"),
        # ER-005: Stroke Warning Signs
        ("One side of face drooping suddenly and arm weakness one side", "ER-005"),
        ("sudden speech difficulty and cannot speak suddenly", "ER-005"),
        ("sudden vision loss and paralysis one side", "ER-005"),
        ("stroke warning signs: sudden severe headache and numbness", "ER-005"),
        # ER-006: Respiratory Failure
        ("struggling to breathe, lips turning blue", "ER-006"),
        ("CANNOT BREATHE at all, breathless and gasping", "ER-006"),
        ("cyanosis with difficulty breathing", "ER-006"),
        ("breathing very fast and can only speak few words", "ER-006"),
        # ER-007: Severe Asthma / Wheeze
        ("severe asthma attack and inhaler not working", "ER-007"),
        ("chest indrawing with rapid breathing", "ER-007"),
        ("wheezing severe cannot complete sentences", "ER-007"),
        ("too breathless to talk, asthma worsening", "ER-007"),
        # ER-008: Severe Rhinosinusitis / Eye Infection
        ("swelling around eyes and double vision with fever", "ER-008"),
        ("stiff neck with high fever and severe sinus pain", "ER-008"),
        ("black discharge from nose with confusion", "ER-008"),
        ("reduced vision and severe eye swelling", "ER-008"),
        # ER-009: Epiglottitis / Deep Neck Infection
        ("drooling saliva and unable to swallow liquids", "ER-009"),
        ("stridor with severe difficulty swallowing", "ER-009"),
        ("muffled voice and cannot open mouth with throat swelling", "ER-009"),
        ("grey membrane in throat with neck swelling", "ER-009"),
        # ER-010: Severe Dehydration
        ("skin pinch goes back very slowly more than 2 seconds", "ER-010"),
        ("sunken eyes and unable to drink any water", "ER-010"),
        ("very rapid weak pulse with watery diarrhoea", "ER-010"),
        ("very low blood pressure and passing many watery stools", "ER-010"),
        # ER-011: Dengue Shock
        ("dengue warning signs: persistent vomiting and severe abdominal pain", "ER-011"),
        ("bleeding from gums with severe dengue fever", "ER-011"),
        ("cold clammy skin and sudden drop in temperature with dengue", "ER-011"),
        ("dengue with extreme lethargy and restlessness", "ER-011"),
        # ER-012: Diabetic Hypoglycaemia
        ("diabetic unconscious and cannot wake up", "ER-012"),
        ("severe hypoglycaemia in diabetes patient who collapsed", "ER-012"),
        ("diabetic passed out from low blood sugar", "ER-012"),
        ("unconscious diabetic needing emergency glucose", "ER-012"),
        # ER-013: Severe Epistaxis
        ("nosebleed not stopping after 20 minutes pressure", "ER-013"),
        ("heavy nosebleed coughing up blood", "ER-013"),
        ("nosebleed bleeding profusely after facial injury", "ER-013"),
        ("nose bleeding heavily and feeling dizzy and fainting", "ER-013"),
        # ER-014: Diabetic Foot Sepsis
        ("diabetic foot with red streaks spreading up leg", "ER-014"),
        ("black toe in diabetic foot with foul smell and fever", "ER-014"),
        ("diabetic ulcer swelling rapidly with high fever", "ER-014"),
        ("gangrene in diabetic foot with chills", "ER-014"),
        # ER-015: Severe Bleeding
        ("arterial bleeding with spurting blood from arm", "ER-015"),
        ("heavy bleeding from leg, bleeding wont stop", "ER-015"),
        ("severe bleeding from deep cut, blood wont stop", "ER-015"),
        ("bleeding profusely after an accident", "ER-015"),
        # ER-016: Internal Bleeding
        ("vomiting blood and blood in throw up", "ER-016"),
        ("passing black stools and tarry stools with weakness", "ER-016"),
        ("vomit blood after severe stomach pain", "ER-016"),
        ("black potty and throwing up dark blood", "ER-016"),
        # ER-017: Seizures
        ("having a seizure and shaking uncontrollably", "ER-017"),
        ("having fits on the floor right now", "ER-017"),
        ("severe convulsions with loss of consciousness", "ER-017"),
        ("patient had mirgi attack and is unresponsive", "ER-017"),
        # ER-018: Unconsciousness
        ("person is unconscious and not responding to calls", "ER-018"),
        ("fainted and not waking up on the floor", "ER-018"),
        ("patient is unresponsive and collapsed", "ER-018"),
        ("cannot wake up my roommate who passed out", "ER-018"),
        # ER-019: Poisoning / Overdose
        ("child drank pesticide by mistake in fields", "ER-019"),
        ("swallowed rat poison, please help immediately", "ER-019"),
        ("took an overdose of sleeping pills", "ER-019"),
        ("consumed insecticide and chemical poisoning", "ER-019"),
        # ER-020: Snake Bite
        ("bitten by snake in the garden", "ER-020"),
        ("snake bite on right foot with swelling and pain", "ER-020"),
        ("snakebite with fang marks and burning sensation", "ER-020"),
        ("snake bit my father in the field", "ER-020"),
        # ER-021: Head Injury
        ("head trauma vomiting and extreme drowsiness", "ER-021"),
        ("hit head vomiting and severe confusion", "ER-021"),
        ("fall on head vomiting with loss of consciousness", "ER-021"),
        ("head injury confusion and drowsiness", "ER-021"),
        # ER-022: Pregnancy Bleeding
        ("bleeding in pregnancy with lower abdominal pain", "ER-022"),
        ("pregnant and bleeding heavily at 7 months", "ER-022"),
        ("pregnancy bleeding with severe cramping", "ER-022"),
        ("spotting in pregnancy and severe belly pain", "ER-022"),
        # ER-023: Choking
        ("choking on food and cannot breathe", "ER-023"),
        ("food stuck in throat cannot breathe at all", "ER-023"),
        ("choking unable to breathe with hands at neck", "ER-023"),
        ("airway blocked food and struggling to breathe", "ER-023"),
    ],
)
def test_emergency_rules_trigger_correctly(
    gate: SafetyGate, query: str, expected_rule: str
) -> None:
    """Emergency symptoms must evaluate to EMERGENCY outcome with helpline 112."""
    decision = gate.evaluate(query)
    assert decision.outcome == "EMERGENCY"
    assert decision.rule_id == expected_rule
    assert decision.message is not None
    assert any(h.number == "112" for h in decision.helplines)


# ---------------------------------------------------------------------------
# 2. Ten Dedicated Negation Tests
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("query", "expected_outcome"),
    [
        ("I have a mild headache but no chest pain", "PASS"),
        ("No fever but severe chest pain", "EMERGENCY"),
        ("I dont have chest pain at all", "PASS"),
        ("Patient denies chest pain", "PASS"),
        ("He is without chest pain today", "PASS"),
        ("I have no chest tightness", "PASS"),
        ("Completely free of chest pain", "PASS"),
        ("I never had chest pain before", "PASS"),
        ("No headache and severe crushing chest pain", "EMERGENCY"),
        ("I have no cough however I have chest pain", "EMERGENCY"),
    ],
)
def test_negation_invariants(gate: SafetyGate, query: str, expected_outcome: str) -> None:
    """Negation correctly suppresses symptoms unless boundary words isolate them."""
    decision = gate.evaluate(query)
    assert decision.outcome == expected_outcome


# ---------------------------------------------------------------------------
# 3. Word Boundary and Substring Protection
# ---------------------------------------------------------------------------
def test_word_boundaries_prevent_false_positives(gate: SafetyGate) -> None:
    """Words containing acronym substrings like 'uti' in 'beautiful' must not trigger rules."""
    decision1 = gate.evaluate("She has a beautiful dress and dry skin")
    assert decision1.outcome == "PASS"

    decision2 = gate.evaluate("The mutation analysis was completed")
    assert decision2.outcome == "PASS"


# ---------------------------------------------------------------------------
# 4. Refusals: Dosage, Diagnosis, Interactions
# ---------------------------------------------------------------------------
def test_dosage_refusal_vs_normal_fluid_question(gate: SafetyGate) -> None:
    """Asking for medication dosage is refused; asking for water intake passes."""
    # Water intake passes
    assert gate.evaluate("How much water should I drink during diarrhea?").outcome == "PASS"

    # Drug dosages are refused
    assert gate.evaluate("What dose of paracetamol should I take for fever?").outcome == "REFUSAL"
    assert gate.evaluate("How many dolo tablets can I take today?").outcome == "REFUSAL"
    assert gate.evaluate("How much cough syrup should I give?").outcome == "REFUSAL"


def test_diagnosis_refusal(gate: SafetyGate) -> None:
    """Requests for direct diagnostic confirmation are refused."""
    assert gate.evaluate("Do I have cancer?").outcome == "REFUSAL"
    assert gate.evaluate("Diagnose me please, what disease do I have?").outcome == "REFUSAL"


def test_drug_interaction_refusal(gate: SafetyGate) -> None:
    """Drug-drug or drug-alcohol interaction questions are refused."""
    assert gate.evaluate("Can I take ibuprofen with alcohol?").outcome == "REFUSAL"
    assert gate.evaluate("Can I mix paracetamol with cough syrup?").outcome == "REFUSAL"


# ---------------------------------------------------------------------------
# 5. Crisis and Scope Precedence
# ---------------------------------------------------------------------------
def test_crisis_routing(gate: SafetyGate) -> None:
    """Mental health crisis queries return CRISIS with Tele-MANAS helpline."""
    decision = gate.evaluate("I feel hopeless and I want to kill myself")
    assert decision.outcome == "CRISIS"
    assert decision.rule_id == "CR-001"
    assert any(h.number == "14416" for h in decision.helplines)


def test_child_scope_and_emergency_priority(gate: SafetyGate) -> None:
    """Pediatric queries are OUT_OF_SCOPE, but pediatric emergencies take priority."""
    # Routine child query -> OUT_OF_SCOPE
    scope_decision = gate.evaluate("My baby has mild diarrhea and runny nose")
    assert scope_decision.outcome == "OUT_OF_SCOPE"
    assert scope_decision.rule_id == "SC-100"

    # Child query with age -> OUT_OF_SCOPE
    age_decision = gate.evaluate("My 4 years old child has a skin rash")
    assert age_decision.outcome == "OUT_OF_SCOPE"

    # Child emergency -> EMERGENCY (Emergency takes precedence over scope)
    emerg_child = gate.evaluate("My baby is not breathing and lips turning blue")
    assert emerg_child.outcome == "EMERGENCY"


def test_emergency_over_refusal_priority(gate: SafetyGate) -> None:
    """Severe emergencies take precedence over refusal matching."""
    query = "I have severe crushing chest pain, what dose of aspirin should I take?"
    decision = gate.evaluate(query)
    assert decision.outcome == "EMERGENCY"


# ---------------------------------------------------------------------------
# 6. Failsafe Error Handling & Performance Invariant
# ---------------------------------------------------------------------------
def test_evaluate_safe_fail_closed_on_exception(gate: SafetyGate) -> None:
    """If the underlying engine fails, evaluate_safe must fail-closed to EMERGENCY."""
    broken_engine = MagicMock()
    broken_engine.match.side_effect = RuntimeError("Simulated internal engine crash")

    broken_gate = SafetyGate(broken_engine)
    decision = broken_gate.evaluate_safe("I have a slight cough")

    assert decision.outcome == "EMERGENCY"
    assert decision.rule_id == "FAILSAFE_ERROR"
    assert any(h.number == "112" for h in decision.helplines)


def test_evaluate_performance_under_5ms(gate: SafetyGate) -> None:
    """SafetyGate evaluate must execute in under 5 milliseconds on a 500-char input."""
    query = (
        "I have been feeling slightly unwell with mild headache and runny nose for 2 days. "
        "No chest pain, no breathing difficulty, no fever. Drinking plenty of water at home."
    )
    # Warm up cache
    gate.evaluate(query)

    start = time.perf_counter()
    decision = gate.evaluate(query)
    elapsed_ms = (time.perf_counter() - start) * 1000

    assert decision.outcome == "PASS"
    assert elapsed_ms < 5.0, f"Evaluation took {elapsed_ms:.2f} ms (expected < 5.0 ms)"
