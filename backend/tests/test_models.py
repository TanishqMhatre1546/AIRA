"""Unit tests for Pydantic models for curated condition files and urgency rules."""

from app.data.models import ConditionDocument, UrgencyRulesFile


def test_condition_document_extra_keys_preserved() -> None:
    """Extra unexpected keys must be tolerated and preserved in model data."""
    raw = {
        "id": "test-condition",
        "condition": "Test Condition",
        "icd_code": "ICD-10-A00",
        "source": {
            "title": "National Guideline",
            "publisher": "MoHFW",
            "edition_year": "2024",
            "url": "https://mohfw.gov.in",
            "custom_source_field": "preserved",
        },
        "sections": [
            {
                "type": "danger_signs",
                "label": "Danger Signs",
                "page": 10,
                "items": ["Severe pain", "High fever"],
                "extra_section_key": 42,
            }
        ],
        "custom_top_level_block": {"key": "val"},
    }

    doc = ConditionDocument.model_validate(raw)
    assert doc.id == "test-condition"
    assert doc.sections[0].page == 10
    # Verify extra fields are preserved
    assert doc.custom_top_level_block == {"key": "val"}  # type: ignore[attr-defined]
    assert doc.source.custom_source_field == "preserved"  # type: ignore[attr-defined]
    assert doc.sections[0].extra_section_key == 42  # type: ignore[attr-defined]


def test_urgency_rules_model_validation() -> None:
    """UrgencyRulesFile parses emergency, see_doctor, and self_care rules."""
    raw = {
        "meta": {"description": "Triage rules", "levels": {"EMERGENCY": "Hospital"}},
        "emergency_rules": [
            {
                "id": "ER-999",
                "condition": "Test Emergency",
                "source_id": "test-condition",
                "source_page": 1,
                "trigger_keywords": ["unconscious", "collapse"],
                "triage_level": "EMERGENCY",
                "response": "Go to hospital.",
            }
        ],
        "see_doctor_rules": [],
        "self_care_rules": [],
    }

    rules_file = UrgencyRulesFile.model_validate(raw)
    assert len(rules_file.emergency_rules) == 1
    assert rules_file.emergency_rules[0].id == "ER-999"
    assert rules_file.emergency_rules[0].triage_level == "EMERGENCY"
