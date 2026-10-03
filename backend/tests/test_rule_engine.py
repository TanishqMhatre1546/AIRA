"""Unit tests for RuleEngine matching, multi-group conjunctions, and negation skipping."""

from app.core.rule_engine import RuleEngine
from app.core.text import normalize, tokens


def test_rule_engine_single_phrase_matching() -> None:
    """RuleEngine detects single trigger phrase matches."""
    rules = [
        {
            "id": "ER-TEST-1",
            "kind": "emergency",
            "condition": "Chest Emergency",
            "match": {"phrases": ["chest pain", "heart attack"], "requires_all": []},
            "negatable": True,
            "response": "Call 112 immediately.",
        }
    ]
    engine = RuleEngine(rules)

    toks = tokens(normalize("I feel severe chest pain right now"))
    hits = engine.match(toks)

    assert len(hits) == 1
    assert hits[0].rule_id == "ER-TEST-1"
    assert hits[0].matched_phrase == "chest pain"
    assert hits[0].skipped_by_negation is False


def test_rule_engine_negatable_skipping() -> None:
    """Negatable rules with confirmed negation are marked as skipped_by_negation."""
    rules = [
        {
            "id": "ER-TEST-1",
            "kind": "emergency",
            "condition": "Chest Emergency",
            "match": {"phrases": ["chest pain"], "requires_all": []},
            "negatable": True,
            "response": "Call 112.",
        },
        {
            "id": "CR-TEST-1",
            "kind": "crisis",
            "condition": "Crisis",
            "match": {"phrases": ["suicide"], "requires_all": []},
            "negatable": False,
            "response": "Call Tele-MANAS.",
        },
    ]
    engine = RuleEngine(rules)

    # 1. Negatable rule skipped
    toks1 = tokens(normalize("I have no chest pain"))
    hits1 = engine.match(toks1)
    assert len(hits1) == 1
    assert hits1[0].skipped_by_negation is True

    # 2. Non-negatable rule fires even if negated
    toks2 = tokens(normalize("no thoughts of suicide"))
    hits2 = engine.match(toks2)
    assert len(hits2) == 1
    assert hits2[0].skipped_by_negation is False


def test_rule_engine_requires_all_multi_group_expansion() -> None:
    """Rules with requires_all require at least one match from every group."""
    rules = [
        {
            "id": "RF-DOSAGE",
            "kind": "refusal",
            "condition": "Dosage",
            "match": {
                "phrases": [],
                "requires_all": [
                    ["how much", "what dose", "how many"],
                    ["tablet", "tablets", "capsule", "@drugs"],
                ],
            },
            "negatable": False,
            "response": "Dosage advice prohibited.",
        }
    ]
    lexicon = ["paracetamol", "dolo", "ibuprofen"]
    engine = RuleEngine(rules, lexicon=lexicon)

    # Hits: "how much" + "dolo"
    toks1 = tokens(normalize("how much dolo should I take?"))
    hits1 = engine.match(toks1)
    assert len(hits1) == 1
    assert hits1[0].rule_id == "RF-DOSAGE"
    assert "how much + dolo" in hits1[0].matched_phrase

    # Miss: "how much water should I drink" (water is not in group 2)
    toks2 = tokens(normalize("how much water should I drink?"))
    hits2 = engine.match(toks2)
    assert len(hits2) == 0
