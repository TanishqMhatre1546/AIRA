"""Unit tests for guideline chunking, extra block processing, and verification filters."""

from app.data.corpus_loader import (
    build_chunks_from_document,
    compute_item_id,
    normalize_text,
    parse_page_number,
    split_items_into_subchunks,
)
from app.data.models import ConditionDocument, ConditionSection, ConditionSource


def _sample_doc() -> ConditionDocument:
    return ConditionDocument(
        id="test-doc",
        condition="Viral Pharyngitis",
        icd_code="ICD-10-J02",
        source=ConditionSource(
            title="STW Sore Throat",
            publisher="ICMR",
            edition_year="2022",
            url="https://stw.icmr.org.in",
        ),
        sections=[
            ConditionSection(
                type="danger_signs",
                label="Emergency Red Flags",
                page=2,
                items=[
                    "Difficulty breathing or swallowing",
                    "Drooling saliva due to inability to swallow",
                ],
            ),
            ConditionSection(
                type="self_care",
                label="Home Care",
                page=None,
                items=["Rest and warm water gargles"],
            ),
        ],
        condition_description="Inflammation of the pharynx causing pain when swallowing.",
        critical_note="Do not prescribe antibiotics for uncomplicated viral sore throat.",
    )


def test_chunk_header_and_item_composition() -> None:
    """Chunks must format text starting with Condition and Section labels."""
    doc = _sample_doc()
    chunks = build_chunks_from_document(doc, allow_unverified=True)

    sec_chunk = next(c for c in chunks if c.section_type == "danger_signs")
    assert sec_chunk.text.startswith("Condition: Viral Pharyngitis. Section: Emergency Red Flags.")
    assert "Difficulty breathing or swallowing." in sec_chunk.text
    assert "Drooling saliva due to inability to swallow." in sec_chunk.text
    assert sec_chunk.page == 2


def test_page_null_handling() -> None:
    """Missing or non-numeric page values must be stored as None without inventing pages."""
    assert parse_page_number(None) is None
    assert parse_page_number("invalid") is None
    assert parse_page_number(5) == 5

    doc = _sample_doc()
    chunks = build_chunks_from_document(doc, allow_unverified=True)
    self_care_chunk = next(c for c in chunks if c.section_type == "self_care")
    assert self_care_chunk.page is None


def test_urticaria_dict_condition_description() -> None:
    """Dictionary condition_description (such as in urticaria) is parsed into overview chunks."""
    doc = ConditionDocument(
        id="icmr-stw-urticaria",
        condition="Urticaria and Angioedema",
        icd_code="ICD-10-L50",
        source=ConditionSource(
            title="STW Urticaria",
            publisher="ICMR",
            edition_year="2022",
            url="https://stw.icmr.org.in",
        ),
        condition_description={
            "urticaria": "Sudden appearance of itchy wheals on the skin.",
            "angioedema": "Sudden deep swelling of the skin and mucous membranes.",
        },
        sections=[],
    )

    chunks = build_chunks_from_document(doc, allow_unverified=True)
    assert len(chunks) == 1
    assert chunks[0].section_type == "overview"
    assert "Urticaria: Sudden appearance of itchy wheals" in chunks[0].text
    assert "Angioedema: Sudden deep swelling" in chunks[0].text


def test_word_limit_subchunk_splitting() -> None:
    """Long sections exceeding ~180 words are split cleanly at item boundaries."""
    long_sent = "Clinical observation regarding home management precautions."
    items = [f"Bullet item {i}: {long_sent}" for i in range(25)]
    item_ids = [f"id_{i}" for i in range(25)]

    header = "Condition: Test. Section: Long List."
    subchunks = split_items_into_subchunks(header, items, item_ids)

    assert len(subchunks) > 1
    for text, ids in subchunks:
        assert text.startswith(header)
        assert len(ids) > 0


def test_verified_only_filter() -> None:
    """Unverified items are excluded when allow_unverified is False, dropping empty chunks."""
    doc = _sample_doc()
    item_norm = normalize_text("Difficulty breathing or swallowing")
    verified_id = compute_item_id("test-doc", "danger_signs", 2, item_norm)

    chunks = build_chunks_from_document(
        doc,
        verified_item_ids={verified_id},
        allow_unverified=False,
    )

    assert len(chunks) == 1
    assert chunks[0].section_type == "danger_signs"
    assert "Difficulty breathing or swallowing." in chunks[0].text
    assert "Drooling saliva" not in chunks[0].text
