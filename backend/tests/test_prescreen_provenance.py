"""Unit tests for provenance pre-screening tool."""

import csv
from pathlib import Path

import pymupdf

from scripts.prescreen_provenance import (
    ConditionSourceConfig,
    classify_suggestion,
    compute_longest_common_subsequence,
    compute_longest_contiguous_sequence,
    find_best_match_in_page,
    has_extractable_text,
    load_source_map,
    normalize_text,
    prescreen_provenance,
    write_prescreen_csv,
    write_prescreen_markdown,
)


def test_normalize_text_expands_ligatures_and_removes_punctuation() -> None:
    """Normalization must decompose ligatures, strip punctuation, and lowercase."""
    raw = "Fluid: check for \ufb02uid loss! Sunken-eyes, lethargy."
    expected = "fluid check for fluid loss sunken eyes lethargy"
    assert normalize_text(raw) == expected


def test_compute_longest_common_subsequence() -> None:
    """LCS must calculate word sequence length preserving relative order."""
    assert compute_longest_common_subsequence([], ["a", "b"]) == 0
    assert compute_longest_common_subsequence(["a", "b", "c"], []) == 0

    seq_a = ["severe", "chest", "pain", "lasting", "30", "minutes"]
    seq_b = ["severe", "crushing", "chest", "pain", "lasting", "more", "than", "30", "minutes"]
    assert compute_longest_common_subsequence(seq_a, seq_b) == 6


def test_compute_longest_contiguous_sequence() -> None:
    """Longest contiguous sequence must find uninterrupted word matching slice."""
    a = ["pinch", "the", "skin", "on", "the", "abdomen"]
    b = ["doctor", "will", "pinch", "the", "skin", "on", "the", "abdomen", "gently"]
    length, start_b, end_b = compute_longest_contiguous_sequence(a, b)
    assert length == 6
    assert start_b == 2
    assert end_b == 8
    assert b[start_b:end_b] == a


def test_find_best_match_in_page_verbatim() -> None:
    """Verbatim text must score high and limit excerpt to at most 20 words."""
    query = "Lethargy or unconsciousness with sunken eyes"
    page = (
        "Patient assessment protocol: Look for danger signs. "
        "Lethargy or unconsciousness with sunken eyes indicate critical emergency. "
        "Refer patient immediately."
    )
    score, excerpt, token_overlap, lcs_ratio = find_best_match_in_page(query, page)
    assert score >= 0.85
    assert token_overlap == 1.0
    assert lcs_ratio == 1.0
    assert len(excerpt.split()) <= 20
    assert "lethargy or unconsciousness with sunken eyes" in excerpt


def test_find_best_match_in_page_no_match() -> None:
    """Completely unrelated text must yield score below 0.5."""
    query = "Lethargy or unconsciousness"
    page = "Apply moisturising ointment twice daily on affected dry skin areas."
    score, excerpt, _, _ = find_best_match_in_page(query, page)
    assert score < 0.5


def test_classify_suggestion_thresholds() -> None:
    """Suggestions must follow exact threshold categories."""
    assert classify_suggestion(0.95, has_text_layer=True) == "likely found"
    assert classify_suggestion(0.85, has_text_layer=True) == "likely found"
    assert classify_suggestion(0.84, has_text_layer=True) == "check"
    assert classify_suggestion(0.50, has_text_layer=True) == "check"
    assert classify_suggestion(0.49, has_text_layer=True) == "not found"
    assert classify_suggestion(0.95, has_text_layer=False) == "no text layer"


def test_has_extractable_text_detects_blank_page() -> None:
    """Pages without text must return False."""
    doc = pymupdf.open()
    doc.new_page()
    assert not has_extractable_text(doc, [1])
    doc.close()


def test_prescreen_provenance_with_fixture_pdf(tmp_path: Path) -> None:
    """End to end test with a small synthetic PDF fixture and provenance records."""
    # 1. Create fixture PDF with 2 pages
    pdf_path = tmp_path / "test_guideline.pdf"
    doc = pymupdf.open()

    # Page 1: Has matching text for item 1
    page1 = doc.new_page()
    page1.insert_text(
        (50, 50),
        "Standard Treatment Workflow. Danger signs: Severe headache with neck stiffness.",
    )

    # Page 2: Has text for item 2, but item 3 is absent
    page2 = doc.new_page()
    page2.insert_text(
        (50, 50),
        "Home management: Drink plenty of clean boiled water and rest.",
    )
    doc.save(pdf_path)
    doc.close()

    # Create empty PDF with no text layer
    empty_pdf_path = tmp_path / "empty_scanned.pdf"
    empty_doc = pymupdf.open()
    empty_doc.new_page()
    empty_doc.save(empty_pdf_path)
    empty_doc.close()

    # 2. Create provenance CSV
    csv_path = tmp_path / "provenance.csv"
    rows = [
        {
            "item_id": "item-001",
            "condition_id": "test-condition",
            "section_type": "danger_signs",
            "page": "1",
            "text": "Severe headache with neck stiffness",
            "status": "unverified",
        },
        {
            "item_id": "item-002",
            "condition_id": "test-condition",
            "section_type": "self_care",
            "page": "2",
            "text": "Drink plenty of clean boiled water",
            "status": "unverified",
        },
        {
            "item_id": "item-003",
            "condition_id": "test-condition",
            "section_type": "danger_signs",
            "page": "1",
            "text": "Cyanosis or blue discolouration on lips",
            "status": "unverified",
        },
        {
            "item_id": "item-004",
            "condition_id": "empty-condition",
            "section_type": "overview",
            "page": "1",
            "text": "Any text on empty scanned document",
            "status": "unverified",
        },
    ]

    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    source_map = {
        "test-condition": ConditionSourceConfig(
            file="test_guideline.pdf",
            page_range=(1, 2),
            page_offset=0,
        ),
        "empty-condition": ConditionSourceConfig(
            file="empty_scanned.pdf",
            page_range=(1, 1),
            page_offset=0,
        ),
    }

    results = prescreen_provenance(csv_path, tmp_path, source_map)
    assert len(results) == 4

    # Item 1: Likely found on page 1
    assert results[0].item_id == "item-001"
    assert results[0].suggestion == "likely found"
    assert results[0].best_match_page == "1"
    assert results[0].match_score >= 0.85

    # Item 2: Likely found on page 2
    assert results[1].item_id == "item-002"
    assert results[1].suggestion == "likely found"
    assert results[1].best_match_page == "2"

    # Item 3: Not found
    assert results[2].item_id == "item-003"
    assert results[2].suggestion == "not found"
    assert results[2].match_score < 0.50

    # Item 4: No text layer
    assert results[3].item_id == "item-004"
    assert results[3].suggestion == "no text layer"

    # Test CSV report generation
    out_csv = tmp_path / "reports" / "prescreen.csv"
    write_prescreen_csv(results, out_csv)
    assert out_csv.exists()

    with open(out_csv, encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        assert len(reader) == 4
        assert reader[0]["suggestion"] == "likely found"
        assert reader[3]["suggestion"] == "no text layer"

    # Test Markdown report generation
    out_md = tmp_path / "reports" / "prescreen.md"
    write_prescreen_markdown(results, out_md)
    assert out_md.exists()

    md_content = out_md.read_text(encoding="utf-8")
    assert "## Items Not Found" in md_content
    assert "item-003" in md_content
    # Ensure "not found" appears before "likely found" in markdown text
    pos_not_found = md_content.find("## Items Not Found")
    pos_likely = md_content.find("## Likely Found Items")
    assert pos_not_found < pos_likely


def test_load_source_map(tmp_path: Path) -> None:
    """Loading source_map.yaml must construct valid ConditionSourceConfig objects."""
    yaml_file = tmp_path / "source_map.yaml"
    yaml_file.write_text(
        """
conditions:
  cond-1:
    file: "sample.pdf"
    page_range: [1, 1]
    page_offset: 0
  cond-2:
    file: "multi.pdf"
    page_range: [27, 33]
    page_offset: 8
""",
        encoding="utf-8",
    )

    mapping = load_source_map(yaml_file)
    assert len(mapping) == 2
    assert mapping["cond-1"].file == "sample.pdf"
    assert mapping["cond-1"].page_range == (1, 1)
    assert mapping["cond-1"].page_offset == 0
    assert mapping["cond-2"].page_range == (27, 33)
    assert mapping["cond-2"].page_offset == 8
