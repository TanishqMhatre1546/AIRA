"""Unit tests for corpus validator rules with failing fixtures for every check."""

import json
from pathlib import Path
from typing import Any

import pytest

from scripts.validate_corpus import CorpusValidator


@pytest.fixture
def test_validator(tmp_path: Path) -> CorpusValidator:
    curated_dir = tmp_path / "curated"
    curated_dir.mkdir()
    lexicon_dir = tmp_path / "lexicon"
    lexicon_dir.mkdir()
    lexicon_file = lexicon_dir / "drug_lexicon.txt"
    lexicon_file.write_text("paracetamol\nibuprofen\namoxicillin\nazithromycin\n", encoding="utf-8")
    return CorpusValidator(curated_dir=curated_dir, lexicon_path=lexicon_file)


def _base_valid_doc() -> dict[str, Any]:
    return {
        "id": "valid-condition",
        "condition": "Valid Condition",
        "icd_code": "ICD-10-A01",
        "source": {
            "title": "Clinical STW",
            "publisher": "MoHFW",
            "edition_year": "2022",
            "url": "https://mohfw.gov.in",
        },
        "sections": [
            {
                "type": "danger_signs",
                "label": "Emergency Warning Signs",
                "page": 1,
                "items": ["Severe difficulty breathing", "Loss of consciousness"],
            }
        ],
    }


def test_check_1_schema_failure(test_validator: CorpusValidator, tmp_path: Path) -> None:
    """Check 1: Malformed JSON or missing required fields fails validation."""
    invalid_file = tmp_path / "curated" / "invalid_schema.json"
    invalid_file.write_text('{"id": "incomplete"}', encoding="utf-8")

    test_validator.validate_condition_file(invalid_file)
    assert any("[Check 1]" in e for e in test_validator.errors)


def test_check_2_empty_items_or_labels(test_validator: CorpusValidator, tmp_path: Path) -> None:
    """Check 2: Empty section labels or empty item strings fail validation."""
    data = _base_valid_doc()
    data["sections"][0]["label"] = "   "
    data["sections"][0]["items"].append("")

    file_path = tmp_path / "curated" / "empty_item.json"
    file_path.write_text(json.dumps(data), encoding="utf-8")

    test_validator.validate_condition_file(file_path)
    assert any("[Check 2]" in e for e in test_validator.errors)


def test_check_3_missing_or_non_integer_page(
    test_validator: CorpusValidator, tmp_path: Path
) -> None:
    """Check 3: Section without a valid positive integer page fails validation."""
    data = _base_valid_doc()
    data["sections"][0]["page"] = None

    file_path = tmp_path / "curated" / "null_page.json"
    file_path.write_text(json.dumps(data), encoding="utf-8")

    test_validator.validate_condition_file(file_path)
    assert any("[Check 3]" in e for e in test_validator.errors)


def test_check_4_duplicate_items(test_validator: CorpusValidator, tmp_path: Path) -> None:
    """Check 4: Duplicate items after normalization fail validation."""
    data = _base_valid_doc()
    data["sections"][0]["items"] = ["Severe chest pain", "  severe CHEST pain  "]

    file_path = tmp_path / "curated" / "duplicate_item.json"
    file_path.write_text(json.dumps(data), encoding="utf-8")

    test_validator.validate_condition_file(file_path)
    assert any("[Check 4]" in e for e in test_validator.errors)


def test_check_5_invalid_rule_source_id(test_validator: CorpusValidator, tmp_path: Path) -> None:
    """Check 5: Urgency rule with unknown source_id fails unless pending clinical review."""
    rules_data = {
        "meta": {"description": "Rules"},
        "emergency_rules": [
            {
                "id": "ER-100",
                "condition": "Condition",
                "source_id": "nonexistent-doc-id",
                "trigger_keywords": ["chest pain"],
                "triage_level": "EMERGENCY",
                "response": "Go to hospital.",
                "review_status": None,
            }
        ],
    }

    rules_file = tmp_path / "curated" / "urgency_rules.json"
    rules_file.write_text(json.dumps(rules_data), encoding="utf-8")

    test_validator.validate_urgency_rules(rules_file)
    assert any("[Check 5]" in e for e in test_validator.errors)


def test_check_6_em_dash_detected(test_validator: CorpusValidator, tmp_path: Path) -> None:
    """Check 6: Unicode em dash (U+2014) in any string fails validation."""
    data = _base_valid_doc()
    data["sections"][0]["label"] = "Emergency Signs \u2014 Go to Hospital"

    file_path = tmp_path / "curated" / "em_dash.json"
    file_path.write_text(json.dumps(data), encoding="utf-8")

    test_validator.validate_condition_file(file_path)
    assert any("[Check 6]" in e for e in test_validator.errors)


def test_check_7_dosing_phrase_detected(test_validator: CorpusValidator, tmp_path: Path) -> None:
    """Check 7: Medical dosing phrases or mg/tablet references fail validation."""
    data = _base_valid_doc()
    data["sections"][0]["items"] = ["Take 500 mg paracetamol twice daily for fever"]

    file_path = tmp_path / "curated" / "dosing.json"
    file_path.write_text(json.dumps(data), encoding="utf-8")

    test_validator.validate_condition_file(file_path)
    assert any("[Check 7]" in e for e in test_validator.errors)


def test_check_8_prohibited_drug_detected(test_validator: CorpusValidator, tmp_path: Path) -> None:
    """Check 8: Drug names not in the allowed list fail validation."""
    data = _base_valid_doc()
    data["sections"][0]["items"] = ["Prescribe amoxicillin for bacterial throat infection"]

    file_path = tmp_path / "curated" / "drug_name.json"
    file_path.write_text(json.dumps(data), encoding="utf-8")

    test_validator.validate_condition_file(file_path)
    assert any("[Check 8]" in e for e in test_validator.errors)
