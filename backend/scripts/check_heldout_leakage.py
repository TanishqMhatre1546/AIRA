#!/usr/bin/env python3
"""Check for potential contamination between held-out test cases and system rules.

Read-only inspection script. Does not modify any file or print held-out cases.
"""

import contextlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml


def extract_words(text: str) -> set[str]:
    """Extract lowercased alphanumeric words of at least 3 characters."""
    return set(re.findall(r"\b[a-z]{3,}\b", text.lower()))


def get_git_first_commit(file_path: Path, repo_root: Path) -> str:
    """Get the earliest commit date for a file."""
    rel_path = file_path.relative_to(repo_root)
    try:
        res = subprocess.run(  # noqa: S603
            ["git", "log", "--reverse", "--format=%as (%h)", "--", str(rel_path)],  # noqa: S607
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        lines = [line.strip() for line in res.stdout.strip().splitlines() if line.strip()]
        return lines[0] if lines else "unknown"
    except Exception as e:
        return f"git error: {e}"


def get_git_last_commit(file_path: Path, repo_root: Path) -> str:
    """Get the latest commit date for a file."""
    rel_path = file_path.relative_to(repo_root)
    try:
        res = subprocess.run(  # noqa: S603
            ["git", "log", "-1", "--format=%as (%h)", "--", str(rel_path)],  # noqa: S607
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        out = res.stdout.strip()
        return out if out else "uncommitted / local"
    except Exception as e:
        return f"git error: {e}"


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent
    backend_dir = repo_root if (repo_root / "data").exists() else repo_root / "backend"

    eval_dir = backend_dir / "eval"
    heldout_dir = eval_dir / "heldout"

    print("=" * 70)
    print("AIRA HELD-OUT CONTAMINATION AND LEAKAGE CHECK (READ-ONLY)")
    print("=" * 70)

    # 1. Collect held-out inputs and words
    heldout_files = sorted(heldout_dir.glob("*.yaml"))
    if not heldout_files:
        print("Error: No held-out files found in eval/heldout/", file=sys.stderr)
        sys.exit(1)

    heldout_texts: list[str] = []
    heldout_words: set[str] = set()

    for hf in heldout_files:
        with open(hf, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        cases = data.get("cases", []) if isinstance(data, dict) else []
        for c in cases:
            if isinstance(c, dict):
                t = (c.get("input") or c.get("text") or "").strip().lower()
                if t:
                    heldout_texts.append(t)
                    heldout_words |= extract_words(t)

    # 2. Collect words from other evaluation files
    other_eval_words: set[str] = set()
    for ef in eval_dir.rglob("*.yaml"):
        if "heldout" in ef.parts:
            continue
        with contextlib.suppress(Exception):
            with open(ef, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            cases = data.get("cases", []) if isinstance(data, dict) else []
            for c in cases:
                if isinstance(c, dict):
                    t = (c.get("input") or c.get("text") or "").strip().lower()
                    if t:
                        other_eval_words |= extract_words(t)

    # 3. Collect words from curated clinical guidelines
    corpus_words: set[str] = set()
    for cf in (backend_dir / "data" / "curated").glob("*.json"):
        if cf.name in ("manifest.json", "urgency_rules.json"):
            continue
        with contextlib.suppress(Exception):
            with open(cf, encoding="utf-8") as f:
                doc = json.load(f)
            raw = json.dumps(doc).lower()
            corpus_words |= extract_words(raw)

    # Distinctive words = in held-out, but not in other evals and not in curated guidelines
    distinctive_words = heldout_words - other_eval_words - corpus_words

    print(f"\nHeld-out test cases found: {len(heldout_texts)} across {len(heldout_files)} files")
    print(f"Total unique words in held-out cases: {len(heldout_words)}")
    print(f"Distinctive words in held-out cases:  {len(distinctive_words)}")

    # 4. Search search_targets for distinctive words
    search_targets: list[Path] = []
    # Lexicon JSON files
    search_targets.extend(sorted((backend_dir / "data" / "lexicon").glob("*.json")))
    # Urgency rules
    urgency_rules_path = backend_dir / "data" / "curated" / "urgency_rules.json"
    if urgency_rules_path.exists():
        search_targets.append(urgency_rules_path)
    # Intake questions
    intake_q_path = backend_dir / "data" / "intake" / "intake_questions.json"
    if intake_q_path.exists():
        search_targets.append(intake_q_path)
    # app/ Python files
    search_targets.extend(sorted((backend_dir / "app").rglob("*.py")))

    word_hits: list[dict[str, Any]] = []
    words_hit_set: set[str] = set()

    for target in search_targets:
        try:
            with open(target, encoding="utf-8") as f:
                for line_no, line in enumerate(f, 1):
                    line_lower = line.lower()
                    for w in distinctive_words:
                        # Whole-word regex match
                        if re.search(rf"\b{re.escape(w)}\b", line_lower):
                            word_hits.append(
                                {
                                    "word": w,
                                    "file": str(target.relative_to(backend_dir)),
                                    "line": line_no,
                                }
                            )
                            words_hit_set.add(w)
        except Exception as e:
            print(f"Warning: could not read {target}: {e}", file=sys.stderr)

    print("\n" + "-" * 70)
    print("DISTINCTIVE WORD SEARCH RESULTS")
    print("-" * 70)
    print(f"Distinctive words found:     {len(distinctive_words)}")
    print(f"Distinctive words with hits: {len(words_hit_set)}")
    print(f"Total hit locations:         {len(word_hits)}")

    if word_hits:
        print("\nWord hits found (warning for clinical review):")
        for hit in word_hits[:50]:
            print(f"  - word: '{hit['word']}', file: {hit['file']}, line: {hit['line']}")
        if len(word_hits) > 50:
            print(f"  ... and {len(word_hits) - 50} more hits")
    else:
        print("\nZero distinctive word hits found in rules, lexicons, or app code.")

    # 5. Check if any rule phrase of 5 or more tokens appears as a substring of any held-out input
    print("\n" + "-" * 70)
    print("RULE PHRASE SUBSTRING CHECK (5+ TOKENS)")
    print("-" * 70)

    rules_file_path = backend_dir / "data" / "curated" / "urgency_rules.json"
    rule_phrase_failures: list[dict[str, str]] = []

    if rules_file_path.exists():
        with open(rules_file_path, encoding="utf-8") as f:
            rdata = json.load(f)
        rules = rdata.get("rules") or (
            rdata.get("emergency_rules", [])
            + rdata.get("see_doctor_rules", [])
            + rdata.get("self_care_rules", [])
        )
        for rule in rules:
            rule_id = rule.get("id", "unknown")
            phrases = rule.get("phrases", [])
            for phrase in phrases:
                toks = phrase.strip().lower().split()
                if len(toks) >= 5:
                    phrase_str = " ".join(toks)
                    for ht in heldout_texts:
                        if phrase_str in ht:
                            rule_phrase_failures.append(
                                {
                                    "rule_id": rule_id,
                                    "phrase": phrase_str,
                                }
                            )

    if rule_phrase_failures:
        print("FAIL: The following 5+ token rule phrases appear as substrings in held-out cases:")
        for rf in rule_phrase_failures:
            print(f'  - Rule {rf["rule_id"]}: "{rf["phrase"]}"')
    else:
        print("PASS: Zero rule phrases with 5 or more tokens appear in held-out test inputs.")

    # 6. Report git commit chronology
    print("\n" + "-" * 70)
    print("GIT CHRONOLOGY (FIRST COMMIT FOR HELDOUT, LAST COMMIT FOR RULES)")
    print("-" * 70)

    print("\nHeld-out Files (First Committed):")
    for hf in heldout_files:
        fc = get_git_first_commit(hf, repo_root)
        print(f"  - {hf.name:<30}: first committed {fc}")

    print("\nRule and Lexicon Files (Last Changed):")
    for rf in [urgency_rules_path] + list((backend_dir / "data" / "lexicon").glob("*.json")):
        lc = get_git_last_commit(rf, repo_root)
        print(f"  - {rf.name:<30}: last changed {lc}")

    print("\n" + "=" * 70)
    if rule_phrase_failures:
        print(
            "Held-out contamination check: FAILED (5+ token rule phrase detected in held-out data)"
        )
        sys.exit(1)
    else:
        print("Held-out contamination check: PASSED (no rule phrase contamination)")
        sys.exit(0)


if __name__ == "__main__":
    main()
