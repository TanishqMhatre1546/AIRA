"""Unit and integration tests for guided clinical intake API endpoints."""

import json
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.core.generator import AnswerGenerator
from app.core.graph import PipelineDeps, build_graph
from app.core.intake import get_all_questions_by_id, strip_question_for_client
from app.core.retriever import Retriever
from app.core.rule_engine import RuleEngine
from app.core.safety_gate import SafetyGate
from app.core.scorer import load_condition_profiles
from app.data.corpus_loader import extract_watch_for_map, load_corpus
from app.data.rules_loader import load_drug_lexicon_list, load_raw_rules
from app.main import create_app


@pytest.fixture(scope="module")
def intake_test_deps() -> PipelineDeps:
    """Fixture providing dependencies configured with intake enabled and loaded intake data."""
    data_dir = Path("data")
    if not data_dir.exists():
        data_dir = Path("backend/data")

    rules = load_raw_rules(data_dir)
    drugs = load_drug_lexicon_list(data_dir)
    scorer_engine = RuleEngine(rules=rules, lexicon=drugs)
    gate = SafetyGate(scorer_engine)
    profiles = load_condition_profiles(data_dir / "lexicon" / "condition_profiles.json")

    chunks = load_corpus(data_dir=data_dir, allow_unverified=True)
    watch_for = extract_watch_for_map(chunks)

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

    test_settings = Settings(
        llm_enabled=False,  # Use extractive mode for deterministic fast tests
        retrieval_min_cosine=-1.0,
        retrieval_min_bm25=0.0,
        intake_enabled=True,
        allow_unverified_content=True,
    )

    retriever = Retriever(
        chunks=chunks,
        matrix=matrix,
        embedder=MockEmbedder(),
        settings=test_settings,
    )
    generator = AnswerGenerator(settings=test_settings)

    intake_path = data_dir / "intake" / "intake_questions.json"
    with open(intake_path, encoding="utf-8") as f:
        intake_data = json.load(f)

    return PipelineDeps(
        gate=gate,
        engine=scorer_engine,
        profiles=profiles,
        watch_for=watch_for,
        retriever=retriever,
        generator=generator,
        settings=test_settings,
        intake_data=intake_data,
        verified_item_ids=set(),
    )


@pytest.fixture
def client_intake_enabled(intake_test_deps: PipelineDeps) -> TestClient:
    """Test client with intake enabled."""
    app = create_app(custom_settings=intake_test_deps.settings)
    app.state.is_ready = True
    app.state.graph = build_graph(intake_test_deps)
    app.state.deps = intake_test_deps
    return TestClient(app)


@pytest.fixture
def client_intake_disabled(intake_test_deps: PipelineDeps) -> TestClient:
    """Test client with intake disabled (v1 default)."""
    disabled_settings = Settings(
        llm_enabled=False,
        retrieval_min_cosine=-1.0,
        retrieval_min_bm25=0.0,
        intake_enabled=False,
    )
    disabled_deps = PipelineDeps(
        gate=intake_test_deps.gate,
        engine=intake_test_deps.engine,
        profiles=intake_test_deps.profiles,
        watch_for=intake_test_deps.watch_for,
        retriever=intake_test_deps.retriever,
        generator=intake_test_deps.generator,
        settings=disabled_settings,
        intake_data=intake_test_deps.intake_data,
    )
    app = create_app(custom_settings=disabled_settings)
    app.state.is_ready = True
    app.state.graph = build_graph(disabled_deps)
    app.state.deps = disabled_deps
    return TestClient(app)


# ---------------------------------------------------------------------------
# Test 1: Intake Disabled by Default returns ANSWER, never FOLLOW_UP
# ---------------------------------------------------------------------------
def test_intake_disabled_by_default(client_intake_disabled: TestClient) -> None:
    resp = client_intake_disabled.post("/api/triage", json={"message": "I have a cough and cold"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["response_type"] != "FOLLOW_UP"
    assert data["response_type"] == "ANSWER"


# ---------------------------------------------------------------------------
# Test 2: Intake Enabled returns FOLLOW_UP with at most 3 questions
# ---------------------------------------------------------------------------
def test_intake_enabled_returns_followup_for_mild_query(client_intake_enabled: TestClient) -> None:
    resp = client_intake_enabled.post("/api/triage", json={"message": "I have a cough and cold"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["response_type"] == "FOLLOW_UP"
    assert 1 <= len(data["questions"]) <= 3
    assert data["allow_text"] is True
    assert data["text_max"] == 300
    assert data["skip_allowed"] is True


# ---------------------------------------------------------------------------
# Test 3: Client Question Options are stripped of internal metadata
# ---------------------------------------------------------------------------
def test_client_question_options_stripped(client_intake_enabled: TestClient) -> None:
    resp = client_intake_enabled.post("/api/triage", json={"message": "I have a cough and cold"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["response_type"] == "FOLLOW_UP"

    forbidden_keys = {
        "rule_id",
        "canonical_phrase",
        "min_level",
        "source_id",
        "source_page",
        "item_id",
    }
    for q in data["questions"]:
        assert "id" in q
        assert "type" in q
        assert "text" in q
        assert "options" in q
        for opt in q["options"]:
            assert set(opt.keys()) == {"id", "label"}
            overlap = set(opt.keys()).intersection(forbidden_keys)
            assert not overlap, f"Forbidden keys leaked in option: {overlap}"


# ---------------------------------------------------------------------------
# Test 4: Duration parsing suppresses duration question
# ---------------------------------------------------------------------------
def test_duration_parsing_suppresses_duration_question(client_intake_enabled: TestClient) -> None:
    # Query with duration stated
    resp = client_intake_enabled.post(
        "/api/triage", json={"message": "I have had a cough for 3 days"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["response_type"] == "FOLLOW_UP"
    q_ids = [q["id"] for q in data["questions"]]
    assert "Q_DURATION" not in q_ids
    assert len(q_ids) == 2  # Condition signs + Risk


# ---------------------------------------------------------------------------
# Test 5: Unknown query gets Area + General Signs + Duration
# ---------------------------------------------------------------------------
def test_unknown_query_gets_area_general_duration(client_intake_enabled: TestClient) -> None:
    resp = client_intake_enabled.post("/api/triage", json={"message": "I feel unwell and tired"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["response_type"] == "FOLLOW_UP"
    q_ids = [q["id"] for q in data["questions"]]
    assert q_ids == ["Q_AREA", "Q_GENERAL_SIGNS", "Q_DURATION"]


# ---------------------------------------------------------------------------
# Test 6: Skip Intake returns exactly the one-step result
# ---------------------------------------------------------------------------
def test_skip_intake_returns_original_result(
    client_intake_enabled: TestClient, client_intake_disabled: TestClient
) -> None:
    query = "I have runny nose and sneezing for 2 days"
    # One-step flow result (intake disabled)
    base_resp = client_intake_disabled.post("/api/triage", json={"message": query})
    base_data = base_resp.json()

    # Skipped intake flow result (intake enabled, skip_intake=True)
    skip_resp = client_intake_enabled.post(
        "/api/triage", json={"message": query, "skip_intake": True}
    )
    skip_data = skip_resp.json()

    assert skip_data["response_type"] == base_data["response_type"]
    assert skip_data["triage_level"] == base_data["triage_level"]


# ---------------------------------------------------------------------------
# Test 7: Direct Emergency message never shows intake
# ---------------------------------------------------------------------------
def test_emergency_message_skips_intake(client_intake_enabled: TestClient) -> None:
    resp = client_intake_enabled.post(
        "/api/triage",
        json={"message": "Severe chest pain radiating to left arm with cold sweats"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["response_type"] == "EMERGENCY"
    assert data["triage_level"] == "EMERGENCY"
    assert len(data.get("questions", [])) == 0


# ---------------------------------------------------------------------------
# Test 8: Round 2 Emergency Option triggers static emergency banner
# ---------------------------------------------------------------------------
def test_round2_emergency_option_triggers_emergency(client_intake_enabled: TestClient) -> None:
    # Round 1: Mild query
    r1 = client_intake_enabled.post("/api/triage", json={"message": "I have had a mild cough"})
    assert r1.status_code == 200
    r1_data = r1.json()
    assert r1_data["response_type"] == "FOLLOW_UP"

    # Round 2: User selects emergency breathing option
    r2 = client_intake_enabled.post(
        "/api/triage",
        json={
            "message": "I have had a mild cough",
            "intake": {
                "answers": [
                    {
                        "question_id": "Q_ACUTE_RESPIRATORY_INFECTIONS_SIGNS",
                        "selected_option_ids": ["opt_ari_cannot_speak"],
                    }
                ]
            },
        },
    )
    assert r2.status_code == 200
    r2_data = r2.json()
    assert r2_data["response_type"] == "EMERGENCY"
    assert r2_data["triage_level"] == "EMERGENCY"
    assert r2_data["mode"] == "static"


# ---------------------------------------------------------------------------
# Test 9: Round 2 Emergency Phrase in Extra Text triggers emergency
# ---------------------------------------------------------------------------
def test_round2_emergency_in_extra_text(client_intake_enabled: TestClient) -> None:
    r2 = client_intake_enabled.post(
        "/api/triage",
        json={
            "message": "I have had a mild cough",
            "intake": {
                "answers": [],
                "extra_text": "I also have severe crushing chest pain radiating to my left arm",
            },
        },
    )
    assert r2.status_code == 200
    data = r2.json()
    assert data["response_type"] == "EMERGENCY"
    assert data["triage_level"] == "EMERGENCY"


# ---------------------------------------------------------------------------
# Test 10: Answers are Escalate-Only (None of these never lowers level)
# ---------------------------------------------------------------------------
def test_answers_are_escalate_only(client_intake_enabled: TestClient) -> None:
    # Base query for acute diarrhea for 10 days gives SEE_DOCTOR
    base = client_intake_enabled.post(
        "/api/triage",
        json={"message": "Watery loose diarrhea for 10 days", "skip_intake": True},
    )
    assert base.json()["triage_level"] == "SEE_DOCTOR"

    # Selecting "None of these" in intake answers cannot lower to SELF_CARE
    round2 = client_intake_enabled.post(
        "/api/triage",
        json={
            "message": "Watery loose diarrhea for 10 days",
            "intake": {
                "answers": [
                    {
                        "question_id": "Q_ACUTE_DIARRHEA_SIGNS",
                        "selected_option_ids": ["opt_diarrhea_none"],
                    }
                ]
            },
        },
    )
    assert round2.status_code == 200
    assert round2.json()["triage_level"] == "SEE_DOCTOR"


# ---------------------------------------------------------------------------
# Test 11: Validation Errors return 422
# ---------------------------------------------------------------------------
def test_validation_422_unknown_question_id(client_intake_enabled: TestClient) -> None:
    resp = client_intake_enabled.post(
        "/api/triage",
        json={
            "message": "Mild cough",
            "intake": {
                "answers": [
                    {
                        "question_id": "Q_NON_EXISTENT_999",
                        "selected_option_ids": ["opt_1"],
                    }
                ]
            },
        },
    )
    assert resp.status_code == 422


def test_validation_422_unknown_option_id(client_intake_enabled: TestClient) -> None:
    resp = client_intake_enabled.post(
        "/api/triage",
        json={
            "message": "Mild cough",
            "intake": {
                "answers": [
                    {
                        "question_id": "Q_DURATION",
                        "selected_option_ids": ["dur_fake_option"],
                    }
                ]
            },
        },
    )
    assert resp.status_code == 422


def test_validation_422_exclusive_combined(client_intake_enabled: TestClient) -> None:
    resp = client_intake_enabled.post(
        "/api/triage",
        json={
            "message": "Mild cough",
            "intake": {
                "answers": [
                    {
                        "question_id": "Q_RISK",
                        "selected_option_ids": ["risk_none", "risk_pregnant"],
                    }
                ]
            },
        },
    )
    assert resp.status_code == 422


def test_validation_422_single_select_multiple_options(client_intake_enabled: TestClient) -> None:
    resp = client_intake_enabled.post(
        "/api/triage",
        json={
            "message": "Mild cough",
            "intake": {
                "answers": [
                    {
                        "question_id": "Q_DURATION",
                        "selected_option_ids": ["dur_1", "dur_2"],
                    }
                ]
            },
        },
    )
    assert resp.status_code == 422


def test_validation_422_extra_text_too_long(client_intake_enabled: TestClient) -> None:
    resp = client_intake_enabled.post(
        "/api/triage",
        json={
            "message": "Mild cough",
            "intake": {
                "answers": [],
                "extra_text": "x" * 301,
            },
        },
    )
    assert resp.status_code == 422


def _find_forbidden_keys(obj: Any, forbidden: set[str], current_path: str = "") -> list[str]:
    found = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            path = f"{current_path}.{k}" if current_path else k
            if k in forbidden:
                found.append(f"Forbidden key '{k}' at {path}")
            found.extend(_find_forbidden_keys(v, forbidden, path))
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            path = f"{current_path}[{idx}]"
            found.extend(_find_forbidden_keys(item, forbidden, path))
    return found


def test_recursive_key_leak_check_all_question_sets(client_intake_enabled: TestClient) -> None:
    forbidden_keys = {
        "canonical_phrase",
        "rule_id",
        "min_level",
        "kind",
        "condition_ids",
        "item_id",
        "source_id",
        "source_page",
        "modifier",
        "duration_days",
    }

    # 1. Test via API for sample queries across conditions and unknown
    test_queries = [
        "I feel unwell and tired",
        "Watery diarrhea",
        "Runny nose and sneezing",
        "Facial pain and sinus headache",
        "Boil on skin with pus",
        "High fever and body ache dengue",
        "Ringworm red itchy rash",
        "High blood sugar and feeling thirsty",
        "Dry itchy patches eczema",
        "Nosebleed stopped bleeding",
        "Dull throbbing headache",
        "High blood pressure dizziness",
        "Sore throat when swallowing",
        "Severe night itch between fingers",
        "Burning urination and pain",
        "Itchy hives and wheals",
    ]

    for q in test_queries:
        resp = client_intake_enabled.post("/api/triage", json={"message": q})
        assert resp.status_code == 200
        data = resp.json()
        assert data["response_type"] == "FOLLOW_UP"
        leaks = _find_forbidden_keys(data, forbidden_keys)
        assert not leaks, f"Forbidden keys leaked for query '{q}': {leaks}"

    # 2. Test strip_question_for_client directly on every question in intake_questions.json
    intake_path = Path("data/intake/intake_questions.json")
    with open(intake_path, encoding="utf-8") as f:
        intake_data = json.load(f)

    all_q_map = get_all_questions_by_id(intake_data)
    for qid, raw_q in all_q_map.items():
        stripped = strip_question_for_client(raw_q)
        leaks = _find_forbidden_keys(stripped, forbidden_keys)
        assert not leaks, f"Forbidden keys leaked in stripped question '{qid}': {leaks}"


def test_no_phi_or_intake_in_logs(
    client_intake_enabled: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    import logging

    private_complaint_query = "UniquePrivateComplaint98765"
    private_complaint_notes = "ConfidentialExtraNotes43210"

    with caplog.at_level(logging.INFO):
        # Round 1
        resp1 = client_intake_enabled.post(
            "/api/triage", json={"message": private_complaint_query}
        )
        assert resp1.status_code == 200

        # Round 2
        resp2 = client_intake_enabled.post(
            "/api/triage",
            json={
                "message": private_complaint_query,
                "intake": {
                    "answers": [
                        {
                            "question_id": "Q_DURATION",
                            "selected_option_ids": ["dur_1"],
                        }
                    ],
                    "extra_text": private_complaint_notes,
                },
            },
        )
        assert resp2.status_code == 200

    # Verify no log record contains confidential data
    for record in caplog.records:
        msg = record.getMessage()
        assert private_complaint_query not in msg, f"Original message found in log: {msg}"
        assert private_complaint_notes not in msg, f"Extra text found in log: {msg}"
        assert "dur_1" not in msg, f"Option ID found in log: {msg}"
        assert "Since today" not in msg, f"Option label found in log: {msg}"

