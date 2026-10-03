"""Loader and parser for urgency rules and drug lexicons."""

import json
from pathlib import Path
from typing import Any

from app.config import settings
from app.core.rule_engine import RuleEngine
from app.core.safety_gate import SafetyGate


def get_default_data_dir() -> Path:
    """Find data directory."""
    return Path(__file__).resolve().parent.parent.parent / "data"


def load_raw_rules(data_dir: Path | None = None) -> list[dict[str, Any]]:
    """Load rule definitions from urgency_rules.json."""
    base_dir = data_dir or settings.data_dir
    rules_file = base_dir / "curated" / "urgency_rules.json"
    if not rules_file.exists():
        rules_file = get_default_data_dir() / "curated" / "urgency_rules.json"

    if not rules_file.exists():
        return []

    with open(rules_file, encoding="utf-8") as f:
        data = json.load(f)

    rules_data: list[dict[str, Any]] = list(data.get("rules", []))
    return rules_data


def load_drug_lexicon_list(data_dir: Path | None = None) -> list[str]:
    """Load drug names from drug_lexicon.txt."""
    base_dir = data_dir or settings.data_dir
    lex_file = base_dir / "lexicon" / "drug_lexicon.txt"
    if not lex_file.exists():
        lex_file = get_default_data_dir() / "lexicon" / "drug_lexicon.txt"

    if not lex_file.exists():
        return []

    drugs: list[str] = []
    with open(lex_file, encoding="utf-8") as f:
        for line in f:
            clean = line.strip().lower()
            if clean and not clean.startswith("#"):
                drugs.append(clean)
    return drugs


def create_safety_gate(data_dir: Path | None = None) -> SafetyGate:
    """Initialize a SafetyGate with loaded rules and lexicon."""
    rules = load_raw_rules(data_dir)
    drugs = load_drug_lexicon_list(data_dir)
    engine = RuleEngine(rules, lexicon=drugs)
    return SafetyGate(engine)
