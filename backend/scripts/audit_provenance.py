"""Audit and synchronize the clinical provenance review sidecar (provenance.csv)."""

import argparse
import csv
import json
import sys
from pathlib import Path

# Ensure backend root is in sys.path
backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app.data.corpus_loader import extract_provenance_items_from_doc, normalize_text  # noqa: E402
from app.data.models import ConditionDocument, ProvenanceRecord  # noqa: E402

PROVENANCE_COLUMNS = [
    "item_id",
    "condition_id",
    "section_type",
    "page",
    "text",
    "status",
    "reviewer",
    "reviewed_on",
    "note",
]


def load_existing_provenance(csv_path: Path) -> dict[str, dict[str, str]]:
    """Load existing provenance CSV records keyed by item_id."""
    records: dict[str, dict[str, str]] = {}
    if not csv_path.exists():
        return records

    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            item_id = row.get("item_id", "").strip()
            if item_id:
                records[item_id] = row
    return records


def audit_corpus(
    curated_dir: Path,
) -> tuple[list[ProvenanceRecord], list[dict[str, str]], list[dict[str, str]]]:
    """Extract all current items and reconcile with existing provenance records."""
    csv_path = curated_dir / "provenance.csv"
    existing = load_existing_provenance(csv_path)

    current_records: list[ProvenanceRecord] = []
    current_ids: set[str] = set()

    for file_path in sorted(curated_dir.glob("*.json")):
        if file_path.name in ("urgency_rules.json", "manifest.json"):
            continue
        with open(file_path, encoding="utf-8") as f:
            raw = json.load(f)
        doc = ConditionDocument.model_validate(raw)
        items = extract_provenance_items_from_doc(doc)
        for item in items:
            current_ids.add(item.item_id)
            if item.item_id in existing:
                prev = existing[item.item_id]
                item.status = prev.get("status", "unverified")  # type: ignore[assignment]
                item.reviewer = prev.get("reviewer") or None
                item.reviewed_on = prev.get("reviewed_on") or None
                item.note = prev.get("note") or None
            current_records.append(item)

    removed_records: list[dict[str, str]] = [
        row for item_id, row in existing.items() if item_id not in current_ids
    ]

    unsupported_records: list[dict[str, str]] = [
        row
        for row in existing.values()
        if row.get("status") == "unsupported" and row.get("item_id") in current_ids
    ]

    return current_records, removed_records, unsupported_records


def write_provenance_csv(records: list[ProvenanceRecord], csv_path: Path) -> None:
    """Write updated provenance records to CSV."""
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=PROVENANCE_COLUMNS)
        writer.writeheader()
        for r in records:
            writer.writerow(
                {
                    "item_id": r.item_id,
                    "condition_id": r.condition_id,
                    "section_type": r.section_type,
                    "page": r.page if r.page is not None else "",
                    "text": r.text,
                    "status": r.status,
                    "reviewer": r.reviewer or "",
                    "reviewed_on": r.reviewed_on or "",
                    "note": r.note or "",
                }
            )


def clean_unsupported_items(curated_dir: Path, unsupported_ids: set[str]) -> None:
    """Remove items marked as unsupported from condition JSON files."""
    if not unsupported_ids:
        print("No unsupported items found to clean.")
        return

    print(f"Cleaning {len(unsupported_ids)} unsupported items from curated JSON files...")
    for file_path in sorted(curated_dir.glob("*.json")):
        if file_path.name in ("urgency_rules.json", "manifest.json"):
            continue
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)

        modified = False
        if "sections" in data and isinstance(data["sections"], list):
            for sec in data["sections"]:
                page = sec.get("page")
                sec_type = sec.get("type", "")
                new_items: list[str] = []
                for itm in sec.get("items", []):
                    from app.data.corpus_loader import compute_item_id

                    norm = normalize_text(itm)
                    i_id = compute_item_id(data.get("id", ""), sec_type, page, norm)
                    if i_id in unsupported_ids:
                        print(f"  Removing from {file_path.name}: '{itm}'")
                        modified = True
                    else:
                        new_items.append(itm)
                sec["items"] = new_items

        if modified:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.write("\n")


def main() -> None:
    """Audit provenance and synchronize provenance.csv."""
    parser = argparse.ArgumentParser(description="Audit and synchronize provenance.csv")
    parser.add_argument(
        "--clean-unsupported",
        action="store_true",
        help="Remove unsupported items from JSON source files",
    )
    args = parser.parse_args()

    curated_dir = backend_root / "data" / "curated"
    csv_path = curated_dir / "provenance.csv"

    records, removed, unsupported = audit_corpus(curated_dir)
    write_provenance_csv(records, csv_path)

    total = len(records)
    verified_count = sum(1 for r in records if r.status == "verified")
    unverified_count = sum(1 for r in records if r.status == "unverified")
    unsupported_count = sum(1 for r in records if r.status == "unsupported")

    print(f"Provenance sidecar updated: {csv_path}")
    print(f"Total active items: {total}")
    print(
        f"  - Verified: {verified_count} ({verified_count / total * 100:.1f}%)" if total else "0%"
    )
    print(f"  - Unverified: {unverified_count}")
    print(f"  - Unsupported: {unsupported_count}")

    if removed:
        print(f"\nReport: {len(removed)} previously tracked items were removed or modified:")
        for r in removed:
            print(f"  - [{r.get('item_id')}] {r.get('condition_id')}: {r.get('text')}")

    if unsupported:
        print(f"\nReport: {len(unsupported)} items marked as UNSUPPORTED:")
        for u in unsupported:
            print(f"  - [{u.get('item_id')}] {u.get('condition_id')}: {u.get('text')}")

        if args.clean_unsupported:
            unsupported_ids = {u["item_id"] for u in unsupported if "item_id" in u}
            clean_unsupported_items(curated_dir, unsupported_ids)


if __name__ == "__main__":
    main()
