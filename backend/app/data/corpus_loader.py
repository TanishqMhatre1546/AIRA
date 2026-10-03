"""Loader, parser, and chunk builder for curated clinical guidelines."""

import csv
import hashlib
import json
import re
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from app.config import settings
from app.data.models import ConditionDocument, GuidelineChunk, ProvenanceRecord

# Maximum approximate word count per chunk before splitting at item boundaries
MAX_CHUNK_WORDS = 180


def normalize_text(text: str) -> str:
    """Normalize text for consistent hashing and comparisons."""
    return re.sub(r"\s+", " ", text.strip().lower())


def compute_item_id(file_id: str, section_type: str, page: int | None, normalized_text: str) -> str:
    """Compute stable 12-character SHA-1 hash for an item."""
    page_str = "" if page is None else str(page)
    raw_key = f"{file_id}|{section_type}|{page_str}|{normalized_text}"
    return hashlib.sha1(raw_key.encode("utf-8")).hexdigest()[:12]  # noqa: S324


def compute_chunk_id(file_id: str, section: str, page: int | None, text: str) -> str:
    """Compute stable SHA-1 hash for a guideline chunk."""
    page_str = "" if page is None else str(page)
    raw_key = f"{file_id}|{section}|{page_str}|{text.strip()}"
    return hashlib.sha1(raw_key.encode("utf-8")).hexdigest()  # noqa: S324


def parse_page_number(page_val: Any) -> int | None:
    """Parse integer page number or return None."""
    if page_val is None:
        return None
    try:
        return int(page_val)
    except (ValueError, TypeError):
        return None


def split_items_into_subchunks(
    header: str, items: Sequence[str], item_ids: Sequence[str]
) -> list[tuple[str, list[str]]]:
    """Split items into subchunks respecting the ~180 words boundary."""
    if not items:
        return []

    header_word_count = len(header.split())
    chunks: list[tuple[str, list[str]]] = []

    curr_items: list[str] = []
    curr_ids: list[str] = []
    curr_words = header_word_count

    for itm, itm_id in zip(items, item_ids, strict=True):
        itm_clean = itm.strip()
        if not itm_clean:
            continue
        # Ensure proper punctuation at item end
        if not itm_clean.endswith((".", "!", "?", ";", ":")):
            itm_clean += "."

        itm_word_count = len(itm_clean.split())
        if curr_items and (curr_words + itm_word_count > MAX_CHUNK_WORDS):
            chunk_body = " ".join(curr_items)
            full_text = f"{header} {chunk_body}".strip()
            chunks.append((full_text, list(curr_ids)))
            curr_items = [itm_clean]
            curr_ids = [itm_id]
            curr_words = header_word_count + itm_word_count
        else:
            curr_items.append(itm_clean)
            curr_ids.append(itm_id)
            curr_words += itm_word_count

    if curr_items:
        chunk_body = " ".join(curr_items)
        full_text = f"{header} {chunk_body}".strip()
        chunks.append((full_text, list(curr_ids)))

    return chunks


def load_provenance_statuses(provenance_path: Path) -> dict[str, str]:
    """Load item verification statuses from provenance.csv."""
    statuses: dict[str, str] = {}
    if not provenance_path.exists():
        return statuses

    with open(provenance_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            item_id = row.get("item_id", "").strip()
            status = row.get("status", "").strip().lower()
            if item_id:
                statuses[item_id] = status
    return statuses


def extract_provenance_items_from_doc(doc: ConditionDocument) -> list[ProvenanceRecord]:
    """Extract all individual reviewable items from a ConditionDocument."""
    records: list[ProvenanceRecord] = []
    file_id = doc.id
    condition_id = file_id

    # 1. Sections
    for section in doc.sections:
        sec_page = parse_page_number(section.page)
        sec_type = section.type
        for item in section.items:
            clean_item = item.strip()
            if not clean_item:
                continue
            norm = normalize_text(clean_item)
            item_id = compute_item_id(file_id, sec_type, sec_page, norm)
            records.append(
                ProvenanceRecord(
                    item_id=item_id,
                    condition_id=condition_id,
                    section_type=sec_type,
                    page=sec_page,
                    text=clean_item,
                    status="unverified",
                )
            )

    # 2. Extra blocks: condition_description
    if doc.condition_description:
        if isinstance(doc.condition_description, str):
            clean = doc.condition_description.strip()
            if clean:
                norm = normalize_text(clean)
                item_id = compute_item_id(file_id, "overview", None, norm)
                records.append(
                    ProvenanceRecord(
                        item_id=item_id,
                        condition_id=condition_id,
                        section_type="overview",
                        page=None,
                        text=clean,
                        status="unverified",
                    )
                )
        elif isinstance(doc.condition_description, dict):
            for k, v in doc.condition_description.items():
                if isinstance(v, str) and v.strip():
                    clean = f"{k.capitalize()}: {v.strip()}"
                    norm = normalize_text(clean)
                    item_id = compute_item_id(file_id, "overview", None, norm)
                    records.append(
                        ProvenanceRecord(
                            item_id=item_id,
                            condition_id=condition_id,
                            section_type="overview",
                            page=None,
                            text=clean,
                            status="unverified",
                        )
                    )

    # 3. Extra blocks: critical_note
    if doc.critical_note:
        text = (
            doc.critical_note
            if isinstance(doc.critical_note, str)
            else json.dumps(doc.critical_note)
        )
        clean = text.strip()
        if clean:
            norm = normalize_text(clean)
            item_id = compute_item_id(file_id, "overview", None, norm)
            records.append(
                ProvenanceRecord(
                    item_id=item_id,
                    condition_id=condition_id,
                    section_type="overview",
                    page=None,
                    text=clean,
                    status="unverified",
                )
            )

    # 4. Extra blocks: reference types
    ref_blocks: list[tuple[str, Any]] = [
        ("screening_note", doc.screening_note),
        ("dehydration_assessment", doc.dehydration_assessment),
        ("high_risk_groups", doc.high_risk_groups),
        ("prevention_note", doc.prevention_note),
        ("scope_note", doc.scope_note),
        ("types_covered", doc.types_covered),
    ]

    for _block_name, block_val in ref_blocks:
        if not block_val:
            continue
        ref_page: int | None = None
        items_to_add: list[str] = []
        if isinstance(block_val, str):
            items_to_add.append(block_val.strip())
        elif isinstance(block_val, list):
            for itm in block_val:
                if isinstance(itm, str) and itm.strip():
                    items_to_add.append(itm.strip())
        elif isinstance(block_val, dict):
            ref_page = parse_page_number(block_val.get("source_page") or block_val.get("page"))
            if "description" in block_val and isinstance(block_val["description"], str):
                items_to_add.append(block_val["description"].strip())
            elif "items" in block_val and isinstance(block_val["items"], list):
                for itm in block_val["items"]:
                    if isinstance(itm, str) and itm.strip():
                        items_to_add.append(itm.strip())
            else:
                for k, v in block_val.items():
                    if k not in ("label", "source_page", "page") and isinstance(v, str):
                        items_to_add.append(f"{k}: {v.strip()}")

        for clean in items_to_add:
            if clean:
                norm = normalize_text(clean)
                item_id = compute_item_id(file_id, "reference", ref_page, norm)
                records.append(
                    ProvenanceRecord(
                        item_id=item_id,
                        condition_id=condition_id,
                        section_type="reference",
                        page=ref_page,
                        text=clean,
                        status="unverified",
                    )
                )

    return records


def build_chunks_from_document(
    doc: ConditionDocument,
    verified_item_ids: set[str] | None = None,
    allow_unverified: bool = False,
) -> list[GuidelineChunk]:
    """Build searchable guideline chunks from a parsed condition document."""
    chunks: list[GuidelineChunk] = []
    file_id = doc.id
    condition_id = file_id
    condition_name = doc.condition
    src = doc.source

    def filter_items(
        items: list[str], sec_type: str, page_num: int | None
    ) -> tuple[list[str], list[str]]:
        kept_items: list[str] = []
        kept_ids: list[str] = []
        for itm in items:
            clean = itm.strip()
            if not clean:
                continue
            norm = normalize_text(clean)
            item_id = compute_item_id(file_id, sec_type, page_num, norm)
            if allow_unverified or (verified_item_ids and item_id in verified_item_ids):
                kept_items.append(clean)
                kept_ids.append(item_id)
        return kept_items, kept_ids

    # 1. Process Sections
    for section in doc.sections:
        sec_page = parse_page_number(section.page)
        sec_type = section.type
        kept_items, kept_ids = filter_items(section.items, sec_type, sec_page)
        if not kept_items:
            continue

        header = f"Condition: {condition_name}. Section: {section.label}."
        subchunks = split_items_into_subchunks(header, kept_items, kept_ids)

        for text, itm_ids in subchunks:
            chunk_id = compute_chunk_id(file_id, section.label, sec_page, text)
            chunks.append(
                GuidelineChunk(
                    chunk_id=chunk_id,
                    condition_id=condition_id,
                    condition=condition_name,
                    section_type=sec_type,
                    label=section.label,
                    text=text,
                    item_ids=itm_ids,
                    source_title=src.title,
                    source_publisher=src.publisher,
                    source_year=src.edition_year,
                    source_url=src.url,
                    page=sec_page,
                )
            )

    # 2. Process Extra Blocks: condition_description
    if doc.condition_description:
        desc_items: list[str] = []
        if isinstance(doc.condition_description, str):
            desc_items = [doc.condition_description.strip()]
        elif isinstance(doc.condition_description, dict):
            desc_items = [
                f"{k.capitalize()}: {v.strip()}"
                for k, v in doc.condition_description.items()
                if isinstance(v, str) and v.strip()
            ]

        kept_items, kept_ids = filter_items(desc_items, "overview", None)
        if kept_items:
            label = "Condition Overview"
            header = f"Condition: {condition_name}. Section: {label}."
            subchunks = split_items_into_subchunks(header, kept_items, kept_ids)
            for text, itm_ids in subchunks:
                chunk_id = compute_chunk_id(file_id, label, None, text)
                chunks.append(
                    GuidelineChunk(
                        chunk_id=chunk_id,
                        condition_id=condition_id,
                        condition=condition_name,
                        section_type="overview",
                        label=label,
                        text=text,
                        item_ids=itm_ids,
                        source_title=src.title,
                        source_publisher=src.publisher,
                        source_year=src.edition_year,
                        source_url=src.url,
                        page=None,
                    )
                )

    # 3. Process Extra Blocks: critical_note
    if doc.critical_note:
        c_text = (
            doc.critical_note
            if isinstance(doc.critical_note, str)
            else json.dumps(doc.critical_note)
        )
        kept_items, kept_ids = filter_items([c_text.strip()], "overview", None)
        if kept_items:
            label = "Critical Note"
            header = f"Condition: {condition_name}. Section: {label}."
            subchunks = split_items_into_subchunks(header, kept_items, kept_ids)
            for text, itm_ids in subchunks:
                chunk_id = compute_chunk_id(file_id, label, None, text)
                chunks.append(
                    GuidelineChunk(
                        chunk_id=chunk_id,
                        condition_id=condition_id,
                        condition=condition_name,
                        section_type="overview",
                        label=label,
                        text=text,
                        item_ids=itm_ids,
                        source_title=src.title,
                        source_publisher=src.publisher,
                        source_year=src.edition_year,
                        source_url=src.url,
                        page=None,
                    )
                )

    # 4. Process Extra Blocks: reference blocks
    ref_blocks: list[tuple[str, Any]] = [
        ("screening_note", doc.screening_note),
        ("dehydration_assessment", doc.dehydration_assessment),
        ("high_risk_groups", doc.high_risk_groups),
        ("prevention_note", doc.prevention_note),
        ("scope_note", doc.scope_note),
        ("types_covered", doc.types_covered),
    ]

    for block_name, block_val in ref_blocks:
        if not block_val:
            continue
        ref_page = None
        label = block_name.replace("_", " ").title()
        items_to_add = []

        if isinstance(block_val, str):
            items_to_add.append(block_val.strip())
        elif isinstance(block_val, list):
            for itm in block_val:
                if isinstance(itm, str) and itm.strip():
                    items_to_add.append(itm.strip())
        elif isinstance(block_val, dict):
            ref_page = parse_page_number(block_val.get("source_page") or block_val.get("page"))
            if "label" in block_val and isinstance(block_val["label"], str):
                label = block_val["label"].strip()
            if "description" in block_val and isinstance(block_val["description"], str):
                items_to_add.append(block_val["description"].strip())
            elif "items" in block_val and isinstance(block_val["items"], list):
                for itm in block_val["items"]:
                    if isinstance(itm, str) and itm.strip():
                        items_to_add.append(itm.strip())
            else:
                for k, v in block_val.items():
                    if k not in ("label", "source_page", "page") and isinstance(v, str):
                        items_to_add.append(f"{k}: {v.strip()}")

        kept_items, kept_ids = filter_items(items_to_add, "reference", ref_page)
        if kept_items:
            header = f"Condition: {condition_name}. Section: {label}."
            subchunks = split_items_into_subchunks(header, kept_items, kept_ids)
            for text, itm_ids in subchunks:
                chunk_id = compute_chunk_id(file_id, label, ref_page, text)
                chunks.append(
                    GuidelineChunk(
                        chunk_id=chunk_id,
                        condition_id=condition_id,
                        condition=condition_name,
                        section_type="reference",
                        label=label,
                        text=text,
                        item_ids=itm_ids,
                        source_title=src.title,
                        source_publisher=src.publisher,
                        source_year=src.edition_year,
                        source_url=src.url,
                        page=ref_page,
                    )
                )

    return chunks


def load_corpus(
    data_dir: Path | None = None,
    allow_unverified: bool | None = None,
) -> list[GuidelineChunk]:
    """Load and parse all condition files in curated data directory into chunks."""
    base_dir = data_dir or settings.data_dir
    curated_dir = base_dir / "curated"
    if not curated_dir.exists():
        curated_dir = base_dir

    allow_unver = (
        allow_unverified if allow_unverified is not None else settings.allow_unverified_content
    )

    verified_ids: set[str] = set()
    if not allow_unver:
        prov_path = curated_dir / "provenance.csv"
        prov_statuses = load_provenance_statuses(prov_path)
        verified_ids = {item_id for item_id, st in prov_statuses.items() if st == "verified"}

    all_chunks: list[GuidelineChunk] = []
    for file_path in sorted(curated_dir.glob("*.json")):
        if file_path.name == "urgency_rules.json" or file_path.name == "manifest.json":
            continue
        try:
            with open(file_path, encoding="utf-8") as f:
                raw = json.load(f)
            doc = ConditionDocument.model_validate(raw)
            chunks = build_chunks_from_document(
                doc,
                verified_item_ids=verified_ids if not allow_unver else None,
                allow_unverified=allow_unver,
            )
            all_chunks.extend(chunks)
        except Exception as e:
            # Re-raise or skip invalid json
            raise ValueError(f"Failed to load condition file {file_path.name}: {e}") from e

    return all_chunks


def load_condition_documents(curated_dir: Path | None = None) -> list[ConditionDocument]:
    """Load and parse all ConditionDocument files from curated directory."""
    base_dir = curated_dir or (settings.data_dir / "curated")
    if not base_dir.exists():
        base_dir = settings.data_dir

    docs: list[ConditionDocument] = []
    for file_path in sorted(base_dir.glob("*.json")):
        if file_path.name in ("urgency_rules.json", "manifest.json"):
            continue
        with open(file_path, encoding="utf-8") as f:
            raw = json.load(f)
        docs.append(ConditionDocument.model_validate(raw))
    return docs


def extract_watch_for_map(chunks: Sequence[GuidelineChunk]) -> dict[str, list[str]]:
    """Extract danger signs and refer urgently items from chunks for scorer."""
    watch_for: dict[str, list[str]] = {}
    for c in chunks:
        if c.section_type in ("danger_signs", "refer_urgently"):
            if c.condition_id not in watch_for:
                watch_for[c.condition_id] = []
            items = [
                s.strip()
                for s in c.text.split(". ")
                if s.strip() and not s.startswith("Condition:") and not s.startswith("Section:")
            ]
            watch_for[c.condition_id].extend(items[:5])
    return watch_for
