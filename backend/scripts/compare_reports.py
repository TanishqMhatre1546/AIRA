#!/usr/bin/env python3
"""Compare evaluation report JSON files for parity and regression detection."""

import json
import sys
from pathlib import Path
from typing import Any

# Metrics where a lower value is better (e.g., error/violation/false positive rates)
LOWER_IS_BETTER_METRICS = {
    "near_miss_false_positive",
    "benign_false_positive",
    "bias_violations",
    "intake_monotonicity_violations",
    "intake_question_invariance_violations",
    "intake_skip_regressions",
}


def load_report(path: Path) -> dict[str, Any]:
    if not path.exists():
        print(f"Error: File not found: {path}", file=sys.stderr)
        sys.exit(1)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: python scripts/compare_reports.py <baseline.json> <candidate.json>")
        sys.exit(1)

    base_path = Path(sys.argv[1])
    cand_path = Path(sys.argv[2])

    base_data = load_report(base_path)
    cand_data = load_report(cand_path)

    base_suites: dict[str, dict[str, Any]] = {
        s["name"]: s for s in base_data.get("suites", [])
    }
    cand_suites: dict[str, dict[str, Any]] = {
        s["name"]: s for s in cand_data.get("suites", [])
    }

    base_names = set(base_suites.keys())
    cand_names = set(cand_suites.keys())

    missing_in_cand = sorted(base_names - cand_names)
    extra_in_cand = sorted(cand_names - base_names)
    common_names = sorted(base_names & cand_names)

    print("=" * 78)
    print("REPORT COMPARISON SUMMARY")
    print(f"Baseline:  {base_path}")
    print(f"Candidate: {cand_path}")
    print("=" * 78)

    has_error = False

    if missing_in_cand:
        has_error = True
        print("\nMissing suites in candidate:")
        for name in missing_in_cand:
            print(f"  - {name}")

    if extra_in_cand:
        print("\nAdditional suites in candidate (not in baseline):")
        for name in extra_in_cand:
            s = cand_suites[name]
            p = s.get("passed")
            tot = s.get("total")
            m_name = s.get("metric_name")
            m_val = s.get("metric_value")
            print(f"  + {name}: {p}/{tot} ({m_name}={m_val})")

    # Table header
    header = (
        f"{'Suite':<28} | {'Base (P/T)':<12} | {'Cand (P/T)':<12} | "
        f"{'Base Metric':<11} | {'Cand Metric':<11} | {'Status':<6}"
    )
    print("\n" + header)
    print("-" * len(header))

    for name in common_names:
        b = base_suites[name]
        c = cand_suites[name]

        b_tot = b.get("total", 0)
        b_pass = b.get("passed", 0)
        b_val = b.get("metric_value", 0.0)
        b_fail = b.get("failures_count", 0)

        c_tot = c.get("total", 0)
        c_pass = c.get("passed", 0)
        c_val = c.get("metric_value", 0.0)
        c_fail = c.get("failures_count", 0)

        m_name = b.get("metric_name", "")
        lower_is_better = m_name in LOWER_IS_BETTER_METRICS

        suite_error = False
        reasons: list[str] = []

        if b_tot != c_tot or b_pass != c_pass:
            suite_error = True
            reasons.append(f"count mismatch ({b_pass}/{b_tot} vs {c_pass}/{c_tot})")

        if b_fail != c_fail or c_fail > b_fail:
            suite_error = True
            reasons.append(f"failures mismatch ({b_fail} vs {c_fail})")

        if lower_is_better:
            if c_val > b_val:
                suite_error = True
                reasons.append(f"metric degraded ({b_val} -> {c_val})")
            elif c_val != b_val:
                suite_error = True
                reasons.append(f"metric changed ({b_val} -> {c_val})")
        else:
            if c_val < b_val:
                suite_error = True
                reasons.append(f"metric degraded ({b_val} -> {c_val})")
            elif c_val != b_val:
                suite_error = True
                reasons.append(f"metric changed ({b_val} -> {c_val})")

        status_str = "FAIL" if suite_error else "PASS"
        if suite_error:
            has_error = True

        b_pt = f"{b_pass}/{b_tot}"
        c_pt = f"{c_pass}/{c_tot}"
        print(f"{name:<28} | {b_pt:<12} | {c_pt:<12} | {b_val:<11} | {c_val:<11} | {status_str:<6}")
        if suite_error:
            for r in reasons:
                print(f"    * REASON: {r}")

    print("-" * len(header))
    if has_error:
        print("Comparison RESULT: FAILED (differences or regressions detected)")
        sys.exit(1)
    else:
        print("Comparison RESULT: PASSED (all baseline suites match perfectly)")
        sys.exit(0)


if __name__ == "__main__":
    main()
