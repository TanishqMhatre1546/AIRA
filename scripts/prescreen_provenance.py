"""Pre-screen clinical provenance records against source PDF documents."""

import argparse
import csv
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pymupdf
import yaml


@dataclass(frozen=True)
class ConditionSourceConfig:
    """Configuration mapping a condition to a source PDF and page range."""

    file: str
    page_range: tuple[int, int]
    page_offset: int = 0


@dataclass
class PrescreenRow:
    """Result row for provenance pre-screening."""

    item_id: str
    condition_id: str
    section_type: str
    page: str
    text: str
    best_match_page: str
    match_score: float
    matched_excerpt: str
    suggestion: str


def normalize_text(text: str) -> str:
    """Normalize text with unicode decomposition, lowercase, and no punctuation."""
    decomposed = unicodedata.normalize("NFKD", text)
    lowercased = decomposed.lower()
    cleaned = re.sub(r"[^\w\s]", " ", lowercased)
    return re.sub(r"\s+", " ", cleaned).strip()


def compute_longest_common_subsequence(a: list[str], b: list[str]) -> int:
    """Compute length of longest common word subsequence using rolling 1D DP."""
    m, n = len(a), len(b)
    if m == 0 or n == 0:
        return 0

    dp = [0] * (n + 1)
    for i in range(1, m + 1):
        prev = 0
        ai = a[i - 1]
        for j in range(1, n + 1):
            temp = dp[j]
            if ai == b[j - 1]:
                dp[j] = prev + 1
            else:
                dp[j] = max(dp[j], dp[j - 1])
            prev = temp
    return dp[n]


def compute_longest_contiguous_sequence(a: list[str], b: list[str]) -> tuple[int, int, int]:
    """Compute length and positions of longest contiguous word sequence."""
    m, n = len(a), len(b)
    if m == 0 or n == 0:
        return 0, 0, 0

    dp = [0] * (n + 1)
    best_len = 0
    best_end_b = 0
    for i in range(1, m + 1):
        new_dp = [0] * (n + 1)
        ai = a[i - 1]
        for j in range(1, n + 1):
            if ai == b[j - 1]:
                val = dp[j - 1] + 1
                new_dp[j] = val
                if val > best_len:
                    best_len = val
                    best_end_b = j
        dp = new_dp

    start_b = max(0, best_end_b - best_len)
    return best_len, start_b, best_end_b


def find_best_match_in_page(
    query: str, page_text: str, max_excerpt_words: int = 20
) -> tuple[float, str, float, float]:
    """Find the best matching passage on a page and return score and excerpt."""
    q_words = normalize_text(query).split()
    p_words = normalize_text(page_text).split()
    if not q_words or not p_words:
        return 0.0, "", 0.0, 0.0

    m, n = len(q_words), len(p_words)
    q_set = set(q_words)

    best_len, contig_start, best_end = compute_longest_contiguous_sequence(q_words, p_words)

    win_len = min(n, max(max_excerpt_words, m + 5))
    is_match = [1 if w in q_set else 0 for w in p_words]
    curr_sum = sum(is_match[:win_len])
    best_sum = curr_sum
    best_win_start = 0

    for i in range(1, n - win_len + 1):
        curr_sum += is_match[i + win_len - 1] - is_match[i - 1]
        if curr_sum > best_sum:
            best_sum = curr_sum
            best_win_start = i

    if best_len >= 3 or best_len >= best_sum:
        win_start = max(0, min(contig_start - 2, n - win_len))
        win_end = min(n, max(best_end + 2, win_start + win_len))
    else:
        win_start = best_win_start
        win_end = min(n, win_start + win_len)

    passage = p_words[win_start:win_end]
    token_overlap = len(q_set & set(passage)) / len(q_set)
    lcs_val = compute_longest_common_subsequence(q_words, passage)
    lcs_ratio = min(1.0, lcs_val / m)

    match_score = round(0.5 * token_overlap + 0.5 * lcs_ratio, 4)
    excerpt_words = passage[:max_excerpt_words]
    matched_excerpt = " ".join(excerpt_words)

    return match_score, matched_excerpt, token_overlap, lcs_ratio


def classify_suggestion(score: float, has_text_layer: bool) -> str:
    """Classify provenance match score into standard categories."""
    if not has_text_layer:
        return "no text layer"
    if score >= 0.85:
        return "likely found"
    if score >= 0.5:
        return "check"
    return "not found"


def load_source_map(yaml_path: Path) -> dict[str, ConditionSourceConfig]:
    """Load condition to source PDF map from YAML."""
    if not yaml_path.exists():
        raise FileNotFoundError(f"Source map file not found: {yaml_path}")

    with open(yaml_path, encoding="utf-8") as f:
        data: dict[str, Any] = yaml.safe_load(f) or {}

    raw_conditions = data.get("conditions", {})
    mapping: dict[str, ConditionSourceConfig] = {}
    for cid, conf in raw_conditions.items():
        pr = conf.get("page_range", [1, 1])
        page_range = (int(pr[0]), int(pr[1]))
        offset = int(conf.get("page_offset", 0))
        mapping[cid] = ConditionSourceConfig(
            file=str(conf["file"]),
            page_range=page_range,
            page_offset=offset,
        )
    return mapping


def has_extractable_text(doc: pymupdf.Document, physical_pages: list[int]) -> bool:
    """Return True if any of the specified physical pages contains non-whitespace text."""
    for p_idx in physical_pages:
        if 1 <= p_idx <= len(doc):
            text = doc[p_idx - 1].get_text().strip()
            if text:
                return True
    return False


def prescreen_provenance(
    provenance_csv_path: Path,
    raw_data_dir: Path,
    source_map: dict[str, ConditionSourceConfig],
) -> list[PrescreenRow]:
    """Execute pre-screening for all rows in provenance.csv."""
    if not provenance_csv_path.exists():
        raise FileNotFoundError(f"Provenance CSV not found: {provenance_csv_path}")

    with open(provenance_csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        input_rows = list(reader)

    # Cache opened documents
    open_docs: dict[str, pymupdf.Document] = {}
    results: list[PrescreenRow] = []

    try:
        for r in input_rows:
            item_id = r["item_id"].strip()
            cid = r["condition_id"].strip()
            section_type = r.get("section_type", "").strip()
            page_str = r.get("page", "").strip()
            text = r.get("text", "").strip()

            if cid not in source_map:
                results.append(
                    PrescreenRow(
                        item_id=item_id,
                        condition_id=cid,
                        section_type=section_type,
                        page=page_str,
                        text=text,
                        best_match_page="",
                        match_score=0.0,
                        matched_excerpt="",
                        suggestion="not found",
                    )
                )
                continue

            config = source_map[cid]
            pdf_path = raw_data_dir / config.file

            if not pdf_path.exists():
                results.append(
                    PrescreenRow(
                        item_id=item_id,
                        condition_id=cid,
                        section_type=section_type,
                        page=page_str,
                        text=text,
                        best_match_page="",
                        match_score=0.0,
                        matched_excerpt="",
                        suggestion="not found",
                    )
                )
                continue

            if config.file not in open_docs:
                open_docs[config.file] = pymupdf.open(pdf_path)
            doc = open_docs[config.file]

            # Determine candidate physical pages
            if page_str.isdigit():
                cited_printed = int(page_str)
                target_phys = cited_printed + config.page_offset
                candidate_phys = [target_phys - 1, target_phys, target_phys + 1]
            else:
                start_p, end_p = config.page_range
                candidate_phys = list(
                    range(start_p + config.page_offset, end_p + config.page_offset + 1)
                )

            valid_phys = [p for p in candidate_phys if 1 <= p <= len(doc)]

            if not has_extractable_text(doc, valid_phys):
                results.append(
                    PrescreenRow(
                        item_id=item_id,
                        condition_id=cid,
                        section_type=section_type,
                        page=page_str,
                        text=text,
                        best_match_page="",
                        match_score=0.0,
                        matched_excerpt="",
                        suggestion="no text layer",
                    )
                )
                continue

            best_score = -1.0
            best_match_page_str = ""
            best_excerpt = ""

            for p_idx in valid_phys:
                page_text = doc[p_idx - 1].get_text()
                score, excerpt, _, _ = find_best_match_in_page(text, page_text)
                if score > best_score:
                    best_score = score
                    best_excerpt = excerpt
                    printed_p = p_idx - config.page_offset
                    best_match_page_str = str(printed_p)

            suggestion = classify_suggestion(best_score, has_text_layer=True)

            results.append(
                PrescreenRow(
                    item_id=item_id,
                    condition_id=cid,
                    section_type=section_type,
                    page=page_str,
                    text=text,
                    best_match_page=best_match_page_str,
                    match_score=best_score,
                    matched_excerpt=best_excerpt,
                    suggestion=suggestion,
                )
            )
    finally:
        for doc in open_docs.values():
            doc.close()

    return results


def write_prescreen_csv(rows: list[PrescreenRow], output_path: Path) -> None:
    """Write prescreen results to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "item_id",
        "condition_id",
        "section_type",
        "page",
        "text",
        "best_match_page",
        "match_score",
        "matched_excerpt",
        "suggestion",
    ]

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(
                {
                    "item_id": r.item_id,
                    "condition_id": r.condition_id,
                    "section_type": r.section_type,
                    "page": r.page,
                    "text": r.text,
                    "best_match_page": r.best_match_page,
                    "match_score": f"{r.match_score:.4f}",
                    "matched_excerpt": r.matched_excerpt,
                    "suggestion": r.suggestion,
                }
            )


def write_prescreen_markdown(rows: list[PrescreenRow], output_path: Path) -> None:
    """Write prescreen summary report in Markdown format with not found items first."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    conditions = sorted({r.condition_id for r in rows})
    counts_by_condition: dict[str, dict[str, int]] = {}

    for cid in conditions:
        counts_by_condition[cid] = {
            "total": 0,
            "likely found": 0,
            "check": 0,
            "not found": 0,
            "no text layer": 0,
        }

    for r in rows:
        c_stats = counts_by_condition[r.condition_id]
        c_stats["total"] += 1
        if r.suggestion in c_stats:
            c_stats[r.suggestion] += 1
        else:
            c_stats["not found"] += 1

    total_all = len(rows)
    likely_all = sum(s["likely found"] for s in counts_by_condition.values())
    check_all = sum(s["check"] for s in counts_by_condition.values())
    not_found_all = sum(s["not found"] for s in counts_by_condition.values())
    no_text_all = sum(s["no text layer"] for s in counts_by_condition.values())

    lines: list[str] = [
        "# Clinical Provenance Pre-Screen Report",
        "",
        "This report provides automated matching scores to support provenance verification.",
        "It does not alter the reviewed status of any item.",
        "",
        "## Summary Counts",
        "",
        (
            "| Condition ID | Total | Likely Found (>=0.85) | Check (0.50-0.85) "
            "| Not Found (<0.50) | No Text Layer |"
        ),
        "| :--- | :--- | :--- | :--- | :--- | :--- |",
    ]

    for cid in conditions:
        st = counts_by_condition[cid]
        lines.append(
            f"| {cid} | {st['total']} | {st['likely found']} | {st['check']} "
            f"| {st['not found']} | {st['no text layer']} |"
        )

    lines.append(
        f"| **Total** | **{total_all}** | **{likely_all}** | **{check_all}** "
        f"| **{not_found_all}** | **{no_text_all}** |"
    )
    lines.append("")

    table_header = (
        "| Item ID | Condition | Section | Page | Text | Score | Best Match Page | Excerpt |"
    )
    table_divider = "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |"

    def make_table_row(r: PrescreenRow) -> str:
        clean_text = r.text.replace("|", "/")
        clean_excerpt = r.matched_excerpt.replace("|", "/")
        return (
            f"| `{r.item_id}` | {r.condition_id} | {r.section_type} | {r.page} | "
            f"{clean_text} | {r.match_score:.2f} | {r.best_match_page} | {clean_excerpt} |"
        )

    # Not found items first
    not_found_rows = [r for r in rows if r.suggestion == "not found"]
    lines.append(f"## Items Not Found ({len(not_found_rows)})")
    lines.append("")
    if not_found_rows:
        lines.append(table_header)
        lines.append(table_divider)
        for r in not_found_rows:
            lines.append(make_table_row(r))
    else:
        lines.append("No items in this category.")
    lines.append("")

    # No text layer items
    no_text_rows = [r for r in rows if r.suggestion == "no text layer"]
    if no_text_rows:
        lines.append(f"## Items with No Text Layer ({len(no_text_rows)})")
        lines.append("")
        lines.append("| Item ID | Condition | Section | Page | Text |")
        lines.append("| :--- | :--- | :--- | :--- | :--- |")
        for r in no_text_rows:
            clean_text = r.text.replace("|", "/")
            lines.append(
                f"| `{r.item_id}` | {r.condition_id} | {r.section_type} | {r.page} | {clean_text} |"
            )
        lines.append("")

    # Check items
    check_rows = [r for r in rows if r.suggestion == "check"]
    lines.append(f"## Items Requiring Check ({len(check_rows)})")
    lines.append("")
    if check_rows:
        lines.append(table_header)
        lines.append(table_divider)
        for r in check_rows:
            lines.append(make_table_row(r))
    else:
        lines.append("No items in this category.")
    lines.append("")

    # Likely found items
    likely_rows = [r for r in rows if r.suggestion == "likely found"]
    lines.append(f"## Likely Found Items ({len(likely_rows)})")
    lines.append("")
    if likely_rows:
        lines.append(table_header)
        lines.append(table_divider)
        for r in likely_rows:
            lines.append(make_table_row(r))
    else:
        lines.append("No items in this category.")
    lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main() -> None:
    """Run provenance pre-screening CLI."""
    parser = argparse.ArgumentParser(
        description="Pre-screen provenance records against source guideline PDFs."
    )
    # Detect repository root whether run from root or backend
    file_dir = Path(__file__).resolve().parent
    if file_dir.name == "scripts" and file_dir.parent.name == "backend":
        repo_root = file_dir.parent.parent
    elif file_dir.name == "scripts":
        repo_root = file_dir.parent
    else:
        repo_root = Path.cwd()

    parser.add_argument(
        "--provenance-csv",
        type=Path,
        default=repo_root / "backend" / "data" / "curated" / "provenance.csv",
        help="Path to provenance.csv",
    )
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=repo_root / "backend" / "data" / "raw",
        help="Path to raw PDFs directory",
    )
    parser.add_argument(
        "--source-map",
        type=Path,
        default=repo_root / "scripts" / "source_map.yaml",
        help="Path to source_map.yaml",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=repo_root / "reports" / "provenance_prescreen.csv",
        help="Path to output CSV report",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=repo_root / "reports" / "provenance_prescreen.md",
        help="Path to output Markdown report",
    )

    args = parser.parse_args()

    source_map = load_source_map(args.source_map)
    rows = prescreen_provenance(
        provenance_csv_path=args.provenance_csv,
        raw_data_dir=args.raw_dir,
        source_map=source_map,
    )

    write_prescreen_csv(rows, args.output_csv)
    write_prescreen_markdown(rows, args.output_md)

    counts: dict[str, int] = {}
    for r in rows:
        counts[r.suggestion] = counts.get(r.suggestion, 0) + 1

    print("Pre-screening completed successfully.")
    print(f"Total rows processed: {len(rows)}")
    for sugg, count in sorted(counts.items()):
        print(f"  {sugg}: {count}")
    print(f"CSV report written to: {args.output_csv}")
    print(f"Markdown report written to: {args.output_md}")


if __name__ == "__main__":
    main()
