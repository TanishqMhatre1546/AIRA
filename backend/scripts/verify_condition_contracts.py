"""Per-condition contract test and completeness verification for AIRA clinical guidelines."""

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

# Ensure backend root is on sys.path
backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app.config import Settings  # noqa: E402
from app.core.generator import AnswerGenerator  # noqa: E402
from app.core.graph import PipelineDeps, build_graph, create_initial_state  # noqa: E402
from app.core.retriever import Retriever  # noqa: E402
from app.core.rule_engine import RuleEngine  # noqa: E402
from app.core.scorer import load_condition_profiles  # noqa: E402
from app.core.validators import extract_items_from_chunk  # noqa: E402
from app.data.corpus_loader import (  # noqa: E402
    load_corpus,
    to_corpus_condition_id,
    to_profile_condition_id,
)
from app.data.rules_loader import (  # noqa: E402
    create_safety_gate,
    load_drug_lexicon_list,
    load_raw_rules,
)

CURATED_DIR = backend_root / "data" / "curated"
PROVENANCE_CSV = CURATED_DIR / "provenance.csv"
TRIAGE_CASES_PATH = backend_root / "eval" / "triage_cases.yaml"
RETRIEVAL_CASES_PATH = backend_root / "eval" / "retrieval_cases.yaml"
REPORTS_DIR = backend_root.parent / "reports"
OUTPUT_REPORT_PATH = REPORTS_DIR / "condition_contract.md"

SECTION_TYPES = ("danger_signs", "self_care", "see_doctor", "refer_urgently")

# 15 condition file mapping: filename -> corpus_id
CONDITION_FILES = [
    "acute_diarrhea.json",
    "acute_respiratory_infections.json",
    "acute_rhinosinusitis.json",
    "bacterial_skin_infections.json",
    "dengue_fever.json",
    "dermatophytosis.json",
    "diabetes_type2.json",
    "eczema_dermatitis.json",
    "epistaxis_nosebleed.json",
    "headache.json",
    "hypertension.json",
    "pharyngitis_sore_throat.json",
    "scabies.json",
    "urinary_tract_infection.json",
    "urticaria_angioedema.json",
]

# 3 curated test queries per condition from eval/triage_cases.yaml and eval/retrieval_cases.yaml
# Format: (profile_key, query_text, expected_triage_level, source_case_id)
CONDITION_TEST_QUERIES: dict[str, list[dict[str, str]]] = {
    "icmr-stw-acute-diarrhea": [
        {
            "id": "TR-DIAR-01",
            "text": "I have loose motions for 1 day, drinking ORS fluids and feeling okay.",
            "expected_level": "SELF_CARE",
        },
        {
            "id": "TR-DIAR-02",
            "text": "Watery diarrhea lasting for 5 days with mild fever.",
            "expected_level": "SEE_DOCTOR",
        },
        {
            "id": "RET-DIAR-01",
            "text": "How to prepare oral rehydration salts ORS for acute diarrhea dehydration?",
            "expected_level": "SELF_CARE",
        },
    ],
    "icmr-stw-acute-respiratory-infections": [
        {
            "id": "TR-RESP-01",
            "text": "Runny nose, sneezing, and mild dry cough for 3 days.",
            "expected_level": "SELF_CARE",
        },
        {
            "id": "TR-RESP-02",
            "text": "Productive cough with thick yellow mucus lasting for 16 days.",
            "expected_level": "SEE_DOCTOR",
        },
        {
            "id": "TR-RESP-03",
            "text": "Persistent cough with high fever and chest discomfort during breathing.",
            "expected_level": "SEE_DOCTOR",
        },
    ],
    "icmr-stw-acute-rhinosinusitis": [
        {
            "id": "TR-SINU-01",
            "text": "Stuffy blocked nose and mild facial heaviness for 3 days.",
            "expected_level": "SELF_CARE",
        },
        {
            "id": "TR-SINU-02",
            "text": "Sinus pressure and green nasal discharge lasting for 12 days.",
            "expected_level": "SEE_DOCTOR",
        },
        {
            "id": "TR-SINU-04",
            "text": "Mild nasal congestion and forehead ache from seasonal weather change.",
            "expected_level": "SELF_CARE",
        },
    ],
    "icmr-stw-bacterial-skin-infections": [
        {
            "id": "TR-SKIN-02",
            "text": "Spreading painful red skin boil on leg with pus discharge for 4 days.",
            "expected_level": "SEE_DOCTOR",
        },
        {
            "id": "TR-SKIN-03",
            "text": "Multiple painful boils spreading across thigh with fever and warmth.",
            "expected_level": "SEE_DOCTOR",
        },
        {
            "id": "RET-SKIN-02",
            "text": "Spreading redness, warmth, and pus in cellulitis and furuncle",
            "expected_level": "SEE_DOCTOR",
        },
    ],
    "icmr-stw-dengue-fever": [
        {
            "id": "TR-DENG-01",
            "text": "Sudden high fever with retro-orbital eye pain and severe body ache.",
            "expected_level": "SEE_DOCTOR",
        },
        {
            "id": "TR-DENG-02",
            "text": "High fever during dengue season with rash and joint pains on day 3.",
            "expected_level": "SEE_DOCTOR",
        },
        {
            "id": "RET-DENG-01",
            "text": "Rest, fluid intake, and paracetamol for fever management in dengue",
            "expected_level": "SEE_DOCTOR",
        },
    ],
    "icmr-stw-dermatophytosis": [
        {
            "id": "TR-DERM-01",
            "text": "Mild circular itchy red ringworm patch on inner thigh for 3 days.",
            "expected_level": "SEE_DOCTOR",
        },
        {
            "id": "TR-DERM-02",
            "text": "Spreading ringworm covering large body surface for 4 weeks.",
            "expected_level": "SEE_DOCTOR",
        },
        {
            "id": "RET-DERM-01",
            "text": "Hygiene measures, loose cotton clothing, and keeping skin dry for ringworm",
            "expected_level": "SEE_DOCTOR",
        },
    ],
    "icmr-stw-diabetes-type2": [
        {
            "id": "TR-DIAB-02",
            "text": "Adult over 40 seeking guidance on diabetes blood sugar screening.",
            "expected_level": "SEE_DOCTOR",
        },
        {
            "id": "TR-DIAB-03",
            "text": "Diabetic patient has a slow healing non-painful sore on sole of foot.",
            "expected_level": "SEE_DOCTOR",
        },
        {
            "id": "RET-DIAB-01",
            "text": "Dietary management, whole grains, and physical exercise for diabetes care",
            "expected_level": "SEE_DOCTOR",
        },
    ],
    "icmr-stw-eczema-dermatitis": [
        {
            "id": "TR-ECZE-01",
            "text": "Dry itchy flaky skin patches on wrists and inside elbows.",
            "expected_level": "SELF_CARE",
        },
        {
            "id": "TR-ECZE-02",
            "text": "Severe weeping eczema rash with yellow crusts and painful cracks.",
            "expected_level": "SEE_DOCTOR",
        },
        {
            "id": "TR-ECZE-03",
            "text": "Mild contact dermatitis redness on hands after cleaning dishes.",
            "expected_level": "SELF_CARE",
        },
    ],
    "icmr-stw-epistaxis": [
        {
            "id": "TR-EPIS-01",
            "text": "Minor nosebleed from one nostril that stopped in 5 minutes with pressure.",
            "expected_level": "SELF_CARE",
        },
        {
            "id": "TR-EPIS-02",
            "text": "Recurrent nosebleeds occurring 4 times this past week.",
            "expected_level": "SEE_DOCTOR",
        },
        {
            "id": "TR-EPIS-04",
            "text": "Slight specks of blood on tissue paper when gently blowing dry nose.",
            "expected_level": "SELF_CARE",
        },
    ],
    "icmr-stw-headache": [
        {
            "id": "TR-HEAD-01",
            "text": "I have a mild tension headache for 2 days after office work.",
            "expected_level": "SELF_CARE",
        },
        {
            "id": "TR-HEAD-02",
            "text": "Throbbing forehead pain for 10 days that is not going away.",
            "expected_level": "SEE_DOCTOR",
        },
        {
            "id": "TR-HEAD-04",
            "text": "Mild head pain on both sides since yesterday afternoon.",
            "expected_level": "SELF_CARE",
        },
    ],
    "asha-ncd-hypertension": [
        {
            "id": "TR-HYPE-01",
            "text": "Routine blood pressure check measured 148/94 mmHg at community health camp.",
            "expected_level": "SEE_DOCTOR",
        },
        {
            "id": "TR-HYPE-02",
            "text": "Adult seeking medical consultation for newly discovered high blood pressure.",
            "expected_level": "SEE_DOCTOR",
        },
        {
            "id": "RET-HYPE-02",
            "text": "Silent killer asymptomatic nature of high blood pressure and screening",
            "expected_level": "SEE_DOCTOR",
        },
    ],
    "icmr-stw-pharyngitis-sore-throat": [
        {
            "id": "TR-PHAR-01",
            "text": "Scratchy dry sore throat for 1 day, no difficulty breathing.",
            "expected_level": "SELF_CARE",
        },
        {
            "id": "TR-PHAR-02",
            "text": "Throat pain lasting for 6 days with difficulty swallowing food.",
            "expected_level": "SEE_DOCTOR",
        },
        {
            "id": "TR-PHAR-03",
            "text": "Sore throat with fever, swollen neck glands, and white pus spots on tonsils.",
            "expected_level": "SEE_DOCTOR",
        },
    ],
    "icmr-stw-scabies": [
        {
            "id": "TR-SCAB-02",
            "text": "Multiple family members itching with small red burrows on waistline.",
            "expected_level": "SEE_DOCTOR",
        },
        {
            "id": "TR-SCAB-03",
            "text": "Severe night-time itch on hands, genitals, and armpits.",
            "expected_level": "SEE_DOCTOR",
        },
        {
            "id": "RET-SCAB-01",
            "text": (
                "Simultaneous treatment of all household contacts and washing clothes for scabies"
            ),
            "expected_level": "SEE_DOCTOR",
        },
    ],
    "icmr-stw-urinary-tract-infection": [
        {
            "id": "TR-UTI-01",
            "text": "Mild burning sensation during urination and increased frequency for 1 day.",
            "expected_level": "SEE_DOCTOR",
        },
        {
            "id": "TR-UTI-02",
            "text": "Painful urination with lower abdomen discomfort and cloudy urine.",
            "expected_level": "SEE_DOCTOR",
        },
        {
            "id": "TR-UTI-03",
            "text": "Urgent need to pass urine with slight blood in urine.",
            "expected_level": "SEE_DOCTOR",
        },
    ],
    "icmr-stw-urticaria-angioedema": [
        {
            "id": "TR-URTI-01",
            "text": "Itchy red raised skin wheals on back that fade away within hours.",
            "expected_level": "SELF_CARE",
        },
        {
            "id": "TR-URTI-02",
            "text": "Recurrent daily hives and itchy wheals for the past 6 weeks.",
            "expected_level": "SEE_DOCTOR",
        },
        {
            "id": "TR-URTI-03",
            "text": "Mild allergic skin rash with itching after wearing synthetic shirt.",
            "expected_level": "SELF_CARE",
        },
    ],
}


def load_verified_counts() -> dict[tuple[str, str], int]:
    """Load count of verified items per (condition_id, section_type) from provenance.csv."""
    verified_counts: dict[tuple[str, str], int] = {}
    if not PROVENANCE_CSV.exists():
        return verified_counts

    with open(PROVENANCE_CSV, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cid = row.get("condition_id", "").strip()
            stype = row.get("section_type", "").strip()
            status = row.get("status", "").strip().lower()
            if status == "verified":
                verified_counts[(cid, stype)] = verified_counts.get((cid, stype), 0) + 1
    return verified_counts


def create_pipeline() -> tuple[Any, PipelineDeps]:
    """Instantiate pipeline in pure extractive mode (model disabled)."""
    settings = Settings(
        llm_enabled=False,
        retrieval_min_cosine=0.40,
        retrieval_min_bm25=0.0,
        allow_unverified_content=True,
    )
    gate = create_safety_gate()
    rules = load_raw_rules()
    lexicon = load_drug_lexicon_list()
    engine = RuleEngine(rules=rules, lexicon=lexicon)
    profiles = load_condition_profiles()
    chunks = load_corpus(allow_unverified=True)

    # Pre-extract watch-for map for engine
    watch_for: dict[str, list[str]] = {}
    for c in chunks:
        if c.section_type in ("danger_signs", "refer_urgently"):
            watch_for.setdefault(c.condition_id, []).extend(extract_items_from_chunk(c))

    # Dense index mock / numpy matrix
    import numpy as np

    matrix_dim = 768
    matrix = np.zeros((len(chunks), matrix_dim), dtype=np.float32)
    for i in range(len(chunks)):
        matrix[i, i % matrix_dim] = 1.0

    class MockEmbedder:
        def embed_query(self, q: str) -> list[float]:
            vec = [0.0] * matrix_dim
            vec[0] = 1.0
            return vec

    retriever = Retriever(
        chunks=chunks,
        matrix=matrix,
        embedder=MockEmbedder(),
        settings=settings,
    )

    generator = AnswerGenerator(settings=settings)

    deps = PipelineDeps(
        gate=gate,
        engine=engine,
        profiles=profiles,
        watch_for=watch_for,
        retriever=retriever,
        generator=generator,
        settings=settings,
    )
    compiled = build_graph(deps)
    return compiled, deps


def run_condition_contracts() -> tuple[list[dict[str, Any]], bool]:
    """Execute completeness and behavioral checks across all 15 condition documents."""
    verified_map = load_verified_counts()
    compiled_pipeline, deps = create_pipeline()

    # Pre-build lookup of chunks per condition
    condition_chunks: dict[str, list[Any]] = {}
    for ch in deps.retriever.chunks:
        condition_chunks.setdefault(ch.condition_id, []).append(ch)

    results: list[dict[str, Any]] = []
    all_passed = True

    for fname in CONDITION_FILES:
        fpath = CURATED_DIR / fname
        if not fpath.exists():
            results.append(
                {
                    "file": fname,
                    "condition_id": "MISSING",
                    "condition_name": fname,
                    "sections_present": [],
                    "completeness": {},
                    "test_runs": [],
                    "passed": False,
                    "gaps": ["Condition file not found on disk."],
                }
            )
            all_passed = False
            continue

        with open(fpath, encoding="utf-8") as f:
            doc_data = json.load(f)

        cid = doc_data["id"]
        cname = doc_data["condition"]
        source_title = doc_data.get("source", {}).get("title", "")

        # 1. Completeness inspection
        sec_items: dict[str, int] = {}
        sec_verified: dict[str, int] = {}
        for sec in doc_data.get("sections", []):
            stype = sec.get("type")
            items = sec.get("items", [])
            sec_items[stype] = len(items)
            sec_verified[stype] = verified_map.get((cid, stype), 0)

        sections_present = [s for s in SECTION_TYPES if s in sec_items and sec_items[s] > 0]

        # Identify completeness gaps
        gaps: list[str] = []
        for s in SECTION_TYPES:
            if s not in sec_items or sec_items[s] == 0:
                gaps.append(f"Missing {s} section in guideline.")

        if "self_care" not in sec_items or sec_items["self_care"] == 0:
            gaps.append("No self_care section; What to do now is empty.")

        # Verified status note
        total_items = sum(sec_items.values())
        total_verified = sum(sec_verified.values())
        if total_verified == 0 and total_items > 0:
            gaps.append("Clinical review pending: 0 items verified in provenance.csv.")

        # 2. Behavioral verification using 3 messages
        queries = CONDITION_TEST_QUERIES.get(cid, [])
        if not queries:
            gaps.append("No test queries configured for this condition.")
            all_passed = False
            results.append(
                {
                    "file": fname,
                    "condition_id": cid,
                    "condition_name": cname,
                    "sections_present": sections_present,
                    "sec_items": sec_items,
                    "sec_verified": sec_verified,
                    "test_runs": [],
                    "passed": False,
                    "gaps": gaps,
                    "sample_level": "UNKNOWN",
                    "sample_wf_count": 0,
                    "sample_dn_count": 0,
                }
            )
            continue

        test_runs: list[dict[str, Any]] = []
        cond_passed = True

        for q in queries:
            qid = q["id"]
            qtext = q["text"]
            expected_lvl = q["expected_level"]

            init_state = create_initial_state(raw_text=qtext)
            graph_res = compiled_pipeline.invoke(init_state)
            resp = graph_res.get("response")

            score = graph_res.get("score")
            detected_conds = score.conditions if score else []

            # Check 1: Detected condition matches expected condition
            target_corpus_cids = {to_corpus_condition_id(c) for c in detected_conds} | set(
                detected_conds
            )
            cond_matched = cid in target_corpus_cids or any(
                to_profile_condition_id(cid) == to_profile_condition_id(c) for c in detected_conds
            )

            # Check 2: Triage level matches expected level
            lvl_matched = resp.triage_level == expected_lvl

            # Check 3: watch_for is not empty; items from danger_signs/refer_urgently
            wf_claims = resp.sections.watch_for
            wf_not_empty = len(wf_claims) > 0

            # Collect raw danger items for this condition
            condition_danger_items = []
            for sec in doc_data.get("sections", []):
                if sec.get("type") in ("danger_signs", "refer_urgently"):
                    condition_danger_items.extend(sec.get("items", []))

            # Normalize for matching
            norm_danger = {item.strip().lower() for item in condition_danger_items if item.strip()}
            wf_valid_source = True
            for claim in wf_claims:
                txt = claim.text.strip().lower()
                # Check if claim text corresponds to a danger item
                if not any(
                    txt.startswith(d[:30]) or d.startswith(txt[:30]) or txt in d or d in txt
                    for d in norm_danger
                ):
                    wf_valid_source = False
                    break

            # Check 4: guidelines_say/do_now contain only allowed section items
            gs_claims = resp.sections.guidelines_say
            dn_claims = resp.sections.do_now

            # Extract self_care and see_doctor text pools
            condition_self_care = []
            for sec in doc_data.get("sections", []):
                if sec.get("type") == "self_care":
                    condition_self_care.extend(sec.get("items", []))

            norm_self_care = {s.strip().lower() for s in condition_self_care if s.strip()}

            # Danger signs prohibited in guidelines_say and do_now unless EMERGENCY
            no_danger_in_guidelines = True
            if resp.triage_level != "EMERGENCY":
                for claim in gs_claims + dn_claims:
                    txt = claim.text.strip().lower()
                    if any(
                        txt == d or (len(txt) > 20 and txt in d and d not in norm_self_care)
                        for d in norm_danger
                    ):
                        no_danger_in_guidelines = False
                        break

            # Check 5: Every citation points to this condition's source file / title and page
            citations_valid = True
            for cit in resp.citations:
                if cit.title != source_title and source_title not in cit.title:
                    citations_valid = False
                    break
                if cit.page is None or cit.page < 1:
                    citations_valid = False
                    break

            # Check 6: No passage from another condition appears
            no_foreign_passages = True
            for cit in resp.citations:
                if cit.title != source_title:
                    no_foreign_passages = False
                    break

            test_ok = (
                cond_matched
                and lvl_matched
                and wf_not_empty
                and wf_valid_source
                and no_danger_in_guidelines
                and citations_valid
                and no_foreign_passages
            )

            if not test_ok:
                cond_passed = False
                failure_reasons = []
                if not cond_matched:
                    failure_reasons.append(
                        f"Detected {detected_conds} did not match expected {cid}."
                    )
                if not lvl_matched:
                    failure_reasons.append(
                        f"Triage level {resp.triage_level} != expected {expected_lvl}."
                    )
                if not wf_not_empty:
                    failure_reasons.append("watch_for was empty.")
                if not wf_valid_source:
                    failure_reasons.append("watch_for items did not match condition danger signs.")
                if not no_danger_in_guidelines:
                    failure_reasons.append("Danger signs leaked into guidelines_say or do_now.")
                if not citations_valid:
                    failure_reasons.append("Citation does not point to condition source or page.")
                if not no_foreign_passages:
                    failure_reasons.append("Foreign passage from another condition detected.")
                gaps.append(f"Query {qid} failed: {'; '.join(failure_reasons)}")

            test_runs.append(
                {
                    "id": qid,
                    "text": qtext,
                    "expected_level": expected_lvl,
                    "actual_level": resp.triage_level,
                    "passed": test_ok,
                    "wf_count": len(wf_claims),
                    "gs_count": len(gs_claims),
                    "dn_count": len(dn_claims),
                    "cits_count": len(resp.citations),
                }
            )

        if not cond_passed:
            all_passed = False

        sample_run = test_runs[0] if test_runs else {}

        results.append(
            {
                "file": fname,
                "condition_id": cid,
                "condition_name": cname,
                "sections_present": sections_present,
                "sec_items": sec_items,
                "sec_verified": sec_verified,
                "test_runs": test_runs,
                "passed": cond_passed,
                "gaps": gaps,
                "sample_level": sample_run.get("actual_level", "UNKNOWN"),
                "sample_wf_count": sample_run.get("wf_count", 0),
                "sample_dn_count": sample_run.get("dn_count", 0),
            }
        )

    return results, all_passed


def generate_markdown_report(results: list[dict[str, Any]]) -> str:
    """Generate reports/condition_contract.md content with one row per condition."""
    lines: list[str] = [
        "# AIRA Clinical Guidelines: Per-Condition Contract Report",
        "",
        (
            "This report verifies completeness and behavioral contracts across "
            "all 15 curated condition documents in `backend/data/curated/` in extractive mode."
        ),
        "",
        "## Summary Table",
        "",
        "| Condition | File | Level Tested | Sections Present | watch_for | do_now | Status | Gaps |",  # noqa: E501
        "| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :--- |",
    ]

    for r in results:
        cname = r["condition_name"]
        fname = r["file"]
        level = r.get("sample_level", "UNKNOWN")
        secs = ", ".join(r.get("sections_present", []))
        wf_cnt = r.get("sample_wf_count", 0)
        dn_cnt = r.get("sample_dn_count", 0)
        status = "**PASS**" if r.get("passed") else "**FAIL**"
        gaps_list = r.get("gaps", [])
        gaps_str = "; ".join(gaps_list) if gaps_list else "None"

        row = (
            f"| {cname} | `{fname}` | {level} | {secs} | "
            f"{wf_cnt} | {dn_cnt} | {status} | {gaps_str} |"
        )
        lines.append(row)

    lines.extend(
        [
            "",
            "## Section Completeness Detail",
            "",
            "| Condition | danger_signs | self_care | see_doctor | refer_urgently | Total Items | Verified Items |",  # noqa: E501
            "| :--- | :---: | :---: | :---: | :---: | :---: | :---: |",
        ]
    )

    for r in results:
        cname = r["condition_name"]
        items = r.get("sec_items", {})
        verified = r.get("sec_verified", {})
        ds = f"{items.get('danger_signs', 0)} ({verified.get('danger_signs', 0)} ver)"
        sc = f"{items.get('self_care', 0)} ({verified.get('self_care', 0)} ver)"
        sd = f"{items.get('see_doctor', 0)} ({verified.get('see_doctor', 0)} ver)"
        ru = f"{items.get('refer_urgently', 0)} ({verified.get('refer_urgently', 0)} ver)"
        tot = sum(items.values())
        tot_ver = sum(verified.values())
        lines.append(f"| {cname} | {ds} | {sc} | {sd} | {ru} | {tot} | {tot_ver} |")

    lines.extend(
        [
            "",
            "## Identified Gaps and Observations",
            "",
        ]
    )

    has_any_gaps = False
    for r in results:
        gaps = r.get("gaps", [])
        if gaps:
            has_any_gaps = True
            lines.append(f"### {r['condition_name']} (`{r['condition_id']}`)")
            for g in gaps:
                lines.append(f"- {g}")
            lines.append("")

    if not has_any_gaps:
        lines.append("No structural or behavioral gaps identified across the 15 conditions.")

    return "\n".join(lines) + "\n"


def main() -> int:
    """Run verification and write reports/condition_contract.md."""
    parser = argparse.ArgumentParser(
        description="Verify per-condition contracts and generate report."
    )
    parser.parse_args()

    print("Running AIRA per-condition contract verification...")
    results, all_passed = run_condition_contracts()

    # Ensure reports directory exists
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_content = generate_markdown_report(results)
    OUTPUT_REPORT_PATH.write_text(report_content, encoding="utf-8")
    backend_reports = backend_root / "reports"
    backend_reports.mkdir(parents=True, exist_ok=True)
    (backend_reports / "condition_contract.md").write_text(report_content, encoding="utf-8")
    print(f"Report written to: {OUTPUT_REPORT_PATH}")

    total = len(results)
    passed_count = sum(1 for r in results if r["passed"])
    failed_count = total - passed_count
    print(f"Contract results: {passed_count}/{total} conditions PASSED ({failed_count} failed).")

    if not all_passed:
        print("ERROR: One or more condition contracts failed!")
        return 1

    print("All 15 condition contracts passed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
