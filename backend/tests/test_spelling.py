"""Unit tests for pure Python deterministic spelling corrector and candidate matching."""

import time

from app.core.rule_engine import RuleEngine
from app.core.safety_gate import SafetyGate
from app.core.scorer import symptom_urgency_scorer
from app.core.spelling import damerau_levenshtein, get_spelling_corrector
from app.data.rules_loader import load_raw_rules


def test_damerau_levenshtein_distance() -> None:
    """Validate distance calculation including transpositions."""
    assert damerau_levenshtein("chest", "chest") == 0
    # Adjacent transposition (swap) counts as 1
    assert damerau_levenshtein("pian", "pain") == 1
    # Deletion
    assert damerau_levenshtein("breath", "breathe") == 1
    # Insertion
    assert damerau_levenshtein("vomitting", "vomiting") == 1
    # Substitution
    assert damerau_levenshtein("feaver", "fever") == 1
    # Multiple edits
    assert damerau_levenshtein("headech", "headache") == 2
    # Large difference
    assert damerau_levenshtein("short", "unconscious") > 2


def test_common_words_protection() -> None:
    """Common English words must never be corrected to symptom terms."""
    corrector = get_spelling_corrector()
    # 'cut' is a common word; should never become 'cat' or symptom
    assert corrector.get_token_candidates("cut") == ["cut"]
    # 'chess' is a common word; should never become 'chest'
    assert corrector.get_token_candidates("chess") == ["chess"]
    # Short words <= 3 chars are never corrected
    assert corrector.get_token_candidates("run") == ["run"]
    assert corrector.get_token_candidates("bad") == ["bad"]


def test_token_length_distance_limits() -> None:
    """Tokens 4-6 letters allow distance 1; tokens >= 7 allow distance 2."""
    corrector = get_spelling_corrector()
    # 4 letters (pian -> pain, distance 1)
    cands = corrector.get_token_candidates("pian")
    assert "pain" in cands

    # 4 letters with distance 2 should not match
    # 'pinn' distance to 'pain' is 2
    assert "pain" not in corrector.get_token_candidates("pinn")

    # 7+ letters allows distance 2 (headech -> headache, distance 2)
    cands_head = corrector.get_token_candidates("headech")
    assert "headache" in cands_head


def test_misspellings_reviewed_map() -> None:
    """Explicit entries from misspellings.json are included as candidates."""
    corrector = get_spelling_corrector()
    assert "breathing" in corrector.get_token_candidates("breating")
    assert "breathe" in corrector.get_token_candidates("breath")
    assert "days" in corrector.get_token_candidates("dayz")
    assert "chest" in corrector.get_token_candidates("cheast")


def test_concatenated_token_split() -> None:
    """Missing spaces in compound symptom words are split correctly."""
    corrector = get_spelling_corrector()
    assert corrector.split_concatenated_token("chestpain") == ("chest", "pain")


def test_safety_gate_demo_queries() -> None:
    """Verify safety gate triggers for emergency demo misspellings."""
    engine = RuleEngine(load_raw_rules())
    gate = SafetyGate(engine)

    # 1. chest pian -> Emergency ER-004
    dec1 = gate.evaluate("chest pian")
    assert dec1.outcome == "EMERGENCY"
    assert dec1.was_corrected is True
    assert "pain" in (dec1.corrected_phrase or "")

    # 2. cant breath -> Emergency ER-006
    dec2 = gate.evaluate("cant breath")
    assert dec2.outcome == "EMERGENCY"
    assert dec2.was_corrected is True

    # 3. i am vomitting blood -> Emergency ER-016
    dec3 = gate.evaluate("i am vomitting blood")
    assert dec3.outcome == "EMERGENCY"


def test_safety_gate_negation_on_misspelled_query() -> None:
    """Negation logic applies correctly to misspelled candidate queries."""
    engine = RuleEngine(load_raw_rules())
    gate = SafetyGate(engine)

    # 'no chest pian' should be negated and PASS
    dec = gate.evaluate("no chest pian")
    assert dec.outcome == "PASS"


def test_scorer_demo_case_feaver_headech() -> None:
    """feaver and headech for 8 dayz -> SEE_DOCTOR with correction recorded."""
    engine = RuleEngine(load_raw_rules())
    res = symptom_urgency_scorer("feaver and headech for 8 dayz", engine=engine)
    assert res.level == "SEE_DOCTOR"
    assert "headache" in res.conditions
    assert res.was_corrected is True
    assert "headache" in (res.corrected_phrase or "")


def test_gate_latency_budget() -> None:
    """Gate must stay under 5 ms normally and under 15 ms with corrections."""
    engine = RuleEngine(load_raw_rules())
    gate = SafetyGate(engine)

    # 500-char message without corrections
    normal_text = "I have a mild runny nose and slight sneezing for the past two days at home. " * 6
    t0 = time.perf_counter()
    dec_norm = gate.evaluate(normal_text[:500])
    elapsed_norm = (time.perf_counter() - t0) * 1000
    assert dec_norm.outcome == "PASS"
    assert elapsed_norm < 10.0  # Well within limits

    # 500-char message with multiple corrections
    typo_text = "I have feaver and headech and cheast pian and cant breath and feel dizzy. " * 6
    t1 = time.perf_counter()
    dec_typo = gate.evaluate(typo_text[:500])
    elapsed_typo = (time.perf_counter() - t1) * 1000
    assert dec_typo.outcome == "EMERGENCY"
    assert elapsed_typo < 15.0
