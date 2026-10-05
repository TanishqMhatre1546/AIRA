"""Unit and regression tests verifying per-condition contracts across all 15 curated guidelines."""

from typing import Any

import pytest

from scripts.verify_condition_contracts import run_condition_contracts


@pytest.fixture(scope="module")
def contract_results() -> tuple[list[dict[str, Any]], bool]:
    """Execute contract verification once for the test module."""
    return run_condition_contracts()


def test_all_fifteen_condition_contracts_pass(
    contract_results: tuple[list[dict[str, Any]], bool],
) -> None:
    """Every curated condition file must pass completeness and behavioral contracts."""
    results, all_passed = contract_results
    assert len(results) == 15, f"Expected 15 condition files, found {len(results)}"

    failures = []
    for r in results:
        if not r.get("passed"):
            failures.append(f"{r['condition_id']} ({r['condition_name']}): {r.get('gaps')}")

    assert all_passed, f"Contract failures detected: {failures}"


@pytest.mark.parametrize(
    "condition_index",
    list(range(15)),
)
def test_individual_condition_contract(
    contract_results: tuple[list[dict[str, Any]], bool], condition_index: int
) -> None:
    """Each individual condition must satisfy completeness, watch_for, and level isolation."""
    results, _ = contract_results
    assert condition_index < len(results)
    res = results[condition_index]

    assert res["passed"] is True, f"Condition {res['condition_id']} failed: {res.get('gaps')}"
    assert len(res["sections_present"]) == 4
    assert res["sample_wf_count"] > 0
    assert len(res["test_runs"]) == 3
    assert all(run["passed"] for run in res["test_runs"])
