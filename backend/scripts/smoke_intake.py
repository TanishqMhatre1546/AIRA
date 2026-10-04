#!/usr/bin/env python3
"""Smoke test script for guided intake against a running local AIRA server."""

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


def post_json(url: str, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    req = urllib.request.Request(  # noqa: S310
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310
            data = json.loads(resp.read().decode("utf-8"))
            return resp.status, data
    except urllib.error.HTTPError as e:
        try:
            err_data = json.loads(e.read().decode("utf-8"))
        except Exception:
            err_data = {"error": str(e)}
        return e.code, err_data
    except Exception as e:
        print(f"Connection error to {url}: {e}", file=sys.stderr)
        sys.exit(1)


def find_emergency_option(intake_data_path: Path) -> tuple[str, str]:
    with open(intake_data_path, encoding="utf-8") as f:
        data = json.load(f)
    throat_q = data.get("condition_questions", {}).get("pharyngitis_sore_throat", {})
    qid = throat_q.get("id", "Q_PHARYNGITIS_SORE_THROAT_SIGNS")
    for opt in throat_q.get("options", []):
        if opt.get("min_level") == "EMERGENCY":
            return qid, opt["id"]
    raise RuntimeError("Could not find EMERGENCY option in sore throat question set.")


def main() -> None:
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    triage_url = f"{base_url.rstrip('/')}/api/triage"

    # Locate intake_questions.json
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent
    intake_path = repo_root / "data" / "intake" / "intake_questions.json"
    if not intake_path.exists():
        intake_path = repo_root / "backend" / "data" / "intake" / "intake_questions.json"

    throat_qid, emerg_opt_id = find_emergency_option(intake_path)

    checks = []
    print(f"Running AIRA Guided Intake Smoke Tests against: {triage_url}\n")

    # Check a: 'sore throat for 3 days' returns FOLLOW_UP with at most 3 questions and text area
    status, data = post_json(triage_url, {"message": "sore throat for 3 days"})
    a_pass = (
        status == 200
        and data.get("response_type") == "FOLLOW_UP"
        and len(data.get("questions", [])) <= 3
        and data.get("allow_text") is True
    )
    checks.append(("Check a: Follow-up questions returned (<= 3) with text area", a_pass))

    # Check b: Same message with skip_intake=True returns ANSWER with baseline level
    status, data = post_json(triage_url, {"message": "sore throat for 3 days", "skip_intake": True})
    b_pass = (
        status == 200
        and data.get("response_type") == "ANSWER"
        and data.get("triage_level") == "SELF_CARE"
    )
    checks.append(("Check b: Skip intake returns baseline ANSWER with SELF_CARE", b_pass))

    # Check c: Sore throat with EMERGENCY option returns EMERGENCY static
    payload_c = {
        "message": "sore throat for 3 days",
        "intake": {
            "answers": [
                {
                    "question_id": throat_qid,
                    "selected_option_ids": [emerg_opt_id],
                }
            ]
        },
    }
    status, data = post_json(triage_url, payload_c)
    c_pass = (
        status == 200
        and data.get("response_type") == "EMERGENCY"
        and data.get("mode") == "static"
    )
    checks.append(("Check c: Emergency option escalates to EMERGENCY static", c_pass))

    # Check d: 'severe chest pain' returns EMERGENCY immediately with no questions
    status, data = post_json(triage_url, {"message": "severe chest pain"})
    d_pass = (
        status == 200
        and data.get("response_type") == "EMERGENCY"
        and not data.get("questions")
    )
    checks.append(
        ("Check d: Red flag query returns EMERGENCY immediately with no questions", d_pass)
    )

    # Check e: 'i feel unwell' returns FOLLOW_UP whose first question is Q_AREA
    status, data = post_json(triage_url, {"message": "i feel unwell"})
    qs = data.get("questions", [])
    e_pass = (
        status == 200
        and data.get("response_type") == "FOLLOW_UP"
        and len(qs) > 0
        and qs[0].get("id") == "Q_AREA"
    )
    checks.append(("Check e: Vague query returns FOLLOW_UP with Q_AREA as first question", e_pass))

    # Check f: Emergency phrase placed in the text area returns EMERGENCY
    payload_f = {
        "message": "sore throat for 3 days",
        "intake": {
            "answers": [],
            "extra_text": "crushing chest pain radiating to left arm",
        },
    }
    status, data = post_json(triage_url, payload_f)
    f_pass = (
        status == 200
        and data.get("response_type") == "EMERGENCY"
        and data.get("mode") == "static"
    )
    checks.append(("Check f: Emergency phrase in text area returns EMERGENCY", f_pass))

    # Check g: Unknown option id returns 422
    payload_g = {
        "message": "sore throat for 3 days",
        "intake": {
            "answers": [
                {
                    "question_id": throat_qid,
                    "selected_option_ids": ["invalid_option_xyz_999"],
                }
            ]
        },
    }
    status, data = post_json(triage_url, payload_g)
    g_pass = status == 422
    checks.append(("Check g: Unknown option ID returns HTTP 422", g_pass))

    all_passed = True
    for label, passed in checks:
        status_tag = "PASS" if passed else "FAIL"
        print(f"[{status_tag}] {label}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("All intake smoke tests passed successfully.")
        sys.exit(0)
    else:
        print("One or more smoke tests failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
