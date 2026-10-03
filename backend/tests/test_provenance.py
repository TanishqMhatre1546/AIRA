"""Unit tests for provenance hash stability, reconciliation, and status tracking."""

from pathlib import Path

from app.data.corpus_loader import compute_item_id, normalize_text
from app.data.models import ConditionDocument, ConditionSection, ConditionSource, ProvenanceRecord
from scripts.audit_provenance import audit_corpus, write_provenance_csv


def test_item_id_hash_stability() -> None:
    """The item_id hash must be strictly deterministic given the same inputs."""
    id1 = compute_item_id("doc-1", "danger_signs", 1, "fever with chills")
    id2 = compute_item_id("doc-1", "danger_signs", 1, "fever with chills")
    assert id1 == id2
    assert len(id1) == 12


def test_item_id_resets_on_text_change() -> None:
    """Modifying an item's text must yield a different item_id requiring re-review."""
    id1 = compute_item_id("doc-1", "danger_signs", 1, "fever with chills")
    id2 = compute_item_id("doc-1", "danger_signs", 1, "fever with severe chills")
    assert id1 != id2


def test_reconciliation_preserves_verified_status(tmp_path: Path) -> None:
    """Audit reconciliation must keep verified status and reviewer for unchanged item_id."""
    doc = ConditionDocument(
        id="test-condition",
        condition="Test",
        icd_code="ICD-10",
        source=ConditionSource(
            title="Title", publisher="Pub", edition_year="2022", url="https://example.com"
        ),
        sections=[
            ConditionSection(
                type="danger_signs",
                label="Danger",
                page=1,
                items=["Severe chest pain"],
            )
        ],
    )

    norm = normalize_text("Severe chest pain")
    item_id = compute_item_id("test-condition", "danger_signs", 1, norm)

    # Write initial provenance CSV with verified status
    csv_file = tmp_path / "provenance.csv"
    existing_record = ProvenanceRecord(
        item_id=item_id,
        condition_id="test-condition",
        section_type="danger_signs",
        page=1,
        text="Severe chest pain",
        status="verified",
        reviewer="Dr. Rao",
        reviewed_on="2026-10-01",
        note="Approved",
    )
    write_provenance_csv([existing_record], csv_file)

    # Re-audit
    json_path = tmp_path / "test_condition.json"
    json_path.write_text(doc.model_dump_json(), encoding="utf-8")

    records, removed, unsupported = audit_corpus(tmp_path)
    assert len(records) == 1
    assert records[0].item_id == item_id
    assert records[0].status == "verified"
    assert records[0].reviewer == "Dr. Rao"
    assert len(removed) == 0
