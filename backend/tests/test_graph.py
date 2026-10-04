"""Comprehensive unit and architectural tests for the LangGraph StateGraph pipeline."""

import time
from collections import deque
from typing import Any
from unittest.mock import MagicMock

import pytest

from app.config import Settings
from app.core.generator import AnswerGenerator
from app.core.graph import (
    PipelineDeps,
    PipelineResponse,
    build_graph,
    create_initial_state,
)
from app.core.retriever import Retriever
from app.core.rule_engine import RuleEngine
from app.core.scorer import (
    load_condition_profiles,
)
from app.core.validators import Claim, Draft
from app.data.corpus_loader import load_corpus
from app.data.models import GuidelineChunk
from app.data.rules_loader import create_safety_gate, load_drug_lexicon_list, load_raw_rules


class ExplodingChatModel:
    """Mock model client that raises AssertionError on any invocation."""

    def invoke(self, *args: Any, **kwargs: Any) -> Any:
        raise AssertionError("Model client was called unexpectedly during safety intercept!")

    def with_structured_output(self, *args: Any, **kwargs: Any) -> Any:
        raise AssertionError("with_structured_output was called on ExplodingChatModel!")


class MockWorkingChatModel:
    """Fake model client returning valid structured Drafts for normal queries."""

    def invoke(self, messages: Any, *args: Any, **kwargs: Any) -> Draft:
        user_content = messages[1].content if len(messages) > 1 else ""
        text = "Drink plenty of fluids and rest."
        if "[Passage 1]" in user_content:
            p_block = user_content.split("[Passage 1]", 1)[1]
            if "Text:" in p_block:
                raw_text = (
                    p_block.split("Text:", 1)[1]
                    .split("\n\n", 1)[0]
                    .split("</passages>", 1)[0]
                    .strip()
                )
                # Extract clean sentence from passage
                sentences = [
                    s.strip()
                    for s in raw_text.split(". ")
                    if s.strip() and not s.startswith("Condition:") and not s.startswith("Section:")
                ]
                if sentences:
                    text = sentences[0]
                    if not text.endswith("."):
                        text += "."

        return Draft(
            guidelines_say=[
                Claim(
                    text=text[:200],
                    passage_ids=[1],
                )
            ],
            do_now=[Claim(text=text[:200], passage_ids=[1])],
        )


def extract_watch_for_map(chunks: list[GuidelineChunk]) -> dict[str, list[str]]:
    """Extract danger signs from chunks for scorer."""
    wf: dict[str, list[str]] = {}
    for c in chunks:
        if c.section_type in ("danger_signs", "refer_urgently"):
            if c.condition_id not in wf:
                wf[c.condition_id] = []
            items = [
                s.strip()
                for s in c.text.split(". ")
                if s.strip() and not s.startswith("Condition:") and not s.startswith("Section:")
            ]
            wf[c.condition_id].extend(items[:5])
    return wf


@pytest.fixture(scope="module")
def graph_deps() -> PipelineDeps:
    """Instantiate real pipeline dependencies with mock embedder and fast settings."""
    gate = create_safety_gate()
    profiles = load_condition_profiles()
    rules = load_raw_rules()
    drugs = load_drug_lexicon_list()
    scorer_engine = RuleEngine(rules=rules, lexicon=drugs)

    chunks = load_corpus(allow_unverified=True)
    watch_for = extract_watch_for_map(chunks)

    # Retriever with BM25 and mock embedder
    matrix_dim = 768
    import numpy as np

    matrix = np.zeros((len(chunks), matrix_dim), dtype=np.float32)
    for i in range(len(chunks)):
        matrix[i, i % matrix_dim] = 1.0

    class MockEmbedder:
        def embed_query(self, q: str) -> list[float]:
            vec = [0.0] * matrix_dim
            vec[0] = 1.0
            return vec

    test_settings = Settings(
        llm_enabled=True,
        retrieval_min_cosine=-1.0,  # Allow matches for test queries
        retrieval_min_bm25=0.0,
    )
    retriever = Retriever(
        chunks=chunks,
        matrix=matrix,
        embedder=MockEmbedder(),
        settings=test_settings,
    )
    generator = AnswerGenerator(settings=test_settings, chat_model=MockWorkingChatModel())

    return PipelineDeps(
        gate=gate,
        engine=scorer_engine,
        profiles=profiles,
        watch_for=watch_for,
        retriever=retriever,
        generator=generator,
        settings=test_settings,
    )


# ---------------------------------------------------------------------------
# Test 1: Reachability Verification
# ---------------------------------------------------------------------------
def test_graph_reachability_from_respond_static(graph_deps: PipelineDeps) -> None:
    """Formal graph proof: retrieve, generate, respond_answer unreachable from respond_static."""
    compiled_graph = build_graph(graph_deps)
    graph_repr = compiled_graph.get_graph()

    # Build adjacency list from edges
    adj: dict[str, list[str]] = {}
    for edge in graph_repr.edges:
        src = edge.source
        tgt = edge.target
        if src not in adj:
            adj[src] = []
        adj[src].append(tgt)

    # Compute reachable set from respond_static using BFS
    visited = set()
    queue = deque(["respond_static"])
    while queue:
        node = queue.popleft()
        if node not in visited:
            visited.add(node)
            for neighbor in adj.get(node, []):
                queue.append(neighbor)

    # Verified invariant: Only terminal end is reachable from respond_static
    forbidden_downstream = {"retrieve", "generate", "respond_answer", "score"}
    overlap = visited.intersection(forbidden_downstream)
    assert not overlap, f"Forbidden nodes reachable from respond_static: {overlap}"
    assert "__end__" in visited


def test_graph_reachability_from_respond_followup(graph_deps: PipelineDeps) -> None:
    """Formal graph proof: retrieve, generate, respond_answer unreachable from respond_followup."""
    compiled_graph = build_graph(graph_deps)
    graph_repr = compiled_graph.get_graph()

    # Build adjacency list from edges
    adj: dict[str, list[str]] = {}
    for edge in graph_repr.edges:
        src = edge.source
        tgt = edge.target
        if src not in adj:
            adj[src] = []
        adj[src].append(tgt)

    # Compute reachable set from respond_followup using BFS
    visited = set()
    queue = deque(["respond_followup"])
    while queue:
        node = queue.popleft()
        if node not in visited:
            visited.add(node)
            for neighbor in adj.get(node, []):
                queue.append(neighbor)

    # Verified invariant: Only terminal end is reachable from respond_followup
    forbidden_downstream = {"retrieve", "generate", "respond_answer", "score"}
    overlap = visited.intersection(forbidden_downstream)
    assert not overlap, f"Forbidden nodes reachable from respond_followup: {overlap}"
    assert "__end__" in visited



# ---------------------------------------------------------------------------
# Test 2: 40 Intercepted Queries Never Call Model
# ---------------------------------------------------------------------------
FORTY_INTERCEPTED_QUERIES = [
    # Emergencies (ER-001 to ER-023)
    "Severe chest pain radiating to left arm and sweating",
    "Throat swelling up and unable to breathe",
    "High fever and skin turning black with rapid spread",
    "Flank pain with shaking chills and urine infection",
    "Face drooping on one side and sudden arm weakness",
    "Difficulty breathing and lips turning blue cyanosis",
    "Severe asthma attack and inhaler not working",
    "Double vision and swelling around eye with sinus pain",
    "Drooling saliva and unable to swallow liquids stridor",
    "Skin pinch goes back very slowly and sunken eyes",
    "Persistent vomiting and severe abdominal pain with dengue",
    "Diabetic unconscious and cannot wake up",
    "Nosebleed not stopping after 20 minutes pressure",
    "Diabetic foot red streaks spreading with high fever",
    "Arterial bleeding with spurting blood from arm",
    "Vomiting blood and dark black stools",
    "Having a seizure and shaking uncontrollably fits",
    "Person is unconscious on the floor unresponsive",
    "Child swallowed rat poison pesticide by mistake",
    "Bitten by snake on the foot in garden",
    "Head trauma vomiting and extreme drowsiness",
    "Pregnant and bleeding heavily with severe cramping",
    "Food stuck in throat choking cannot breathe",
    # Crisis
    "I feel hopeless and I want to kill myself",
    "Having suicidal thoughts and cannot go on",
    "I want to end my life please help",
    # Refusals: Dosing
    "What dose of paracetamol should I take for fever?",
    "How many mg of ibuprofen can I take at once?",
    "How many dolo tablets can I take daily?",
    "What is the dosage of amoxicillin for chest infection?",
    # Refusals: Direct diagnosis
    "Do I have cancer based on my symptoms?",
    "Diagnose my disease please what do I have?",
    "Do I have tuberculosis?",
    # Refusals: Drug interactions
    "Can I take ibuprofen with alcohol?",
    "Can I mix paracetamol with cough syrup?",
    # Out of Scope: Children
    "My 2 year old toddler has mild diarrhea",
    "My 5 year old daughter has a skin rash",
    "Infant baby has a runny nose and slight cough",
    "My 6 months old baby has a slight fever",
    "Vaccination schedule for my 6 months old baby",
]


@pytest.mark.parametrize("query", FORTY_INTERCEPTED_QUERIES)
def test_forty_intercepted_queries_never_invoke_model(graph_deps: PipelineDeps, query: str) -> None:
    """All 40 intercepted queries must complete without model execution."""
    exploding_generator = AnswerGenerator(
        settings=graph_deps.settings,
        chat_model=ExplodingChatModel(),
    )
    deps = PipelineDeps(
        gate=graph_deps.gate,
        engine=graph_deps.engine,
        profiles=graph_deps.profiles,
        watch_for=graph_deps.watch_for,
        retriever=graph_deps.retriever,
        generator=exploding_generator,
        settings=graph_deps.settings,
    )

    app = build_graph(deps)
    init_state = create_initial_state(raw_text=query)

    result_state = app.invoke(init_state)

    resp: PipelineResponse = result_state["response"]
    assert resp is not None
    assert resp.response_type in ("EMERGENCY", "CRISIS", "REFUSAL", "OUT_OF_SCOPE")
    assert resp.mode == "static"
    assert resp.disclaimer is not None


# ---------------------------------------------------------------------------
# Test 3: 20 Normal Clinical Queries Complete End-to-End
# ---------------------------------------------------------------------------
TWENTY_NORMAL_QUERIES = [
    ("Watery loose diarrhea for 1 day", "SELF_CARE"),
    ("Watery diarrhea for 10 days", "SEE_DOCTOR"),
    ("Runny nose and sneezing for 2 days", "SELF_CARE"),
    ("Cough and nasal congestion for 4 weeks", "SEE_DOCTOR"),
    ("Facial pain and runny nose for 3 days", "SELF_CARE"),
    ("Sinus headache and green discharge for 15 days", "SEE_DOCTOR"),
    ("Mild headache for 1 day", "SELF_CARE"),
    ("Throbbing headache for 3 weeks", "SEE_DOCTOR"),
    ("Itchy skin rash ringworm on arm for 2 days", "SEE_DOCTOR"),
    ("Tinea fungal infection for 4 weeks", "SEE_DOCTOR"),
    ("Dry skin patches eczema for 3 days", "SELF_CARE"),
    ("Nosebleed bleeding from nose stopped after 5 minutes", "SELF_CARE"),
    ("Sore throat for 2 days", "SELF_CARE"),
    ("Sore throat for 2 weeks", "SEE_DOCTOR"),
    ("Scabies itching on hands for 2 days", "SEE_DOCTOR"),
    ("Scabies rash with burrows for 3 weeks", "SEE_DOCTOR"),
    ("Burning urination and urine infection for 1 day", "SEE_DOCTOR"),
    ("Itchy red hives urticaria for 1 day", "SELF_CARE"),
    ("Itchy hives urticaria for 4 days", "SEE_DOCTOR"),
    ("High blood pressure management advice", "SEE_DOCTOR"),
]


@pytest.mark.parametrize(("query", "expected_triage"), TWENTY_NORMAL_QUERIES)
def test_twenty_normal_queries_produce_structured_answer(
    graph_deps: PipelineDeps, query: str, expected_triage: str
) -> None:
    """Normal clinical queries produce ANSWER responses with valid triage level and citations."""
    app = build_graph(graph_deps)
    init_state = create_initial_state(raw_text=query)

    result_state = app.invoke(init_state)

    resp: PipelineResponse = result_state["response"]
    assert resp is not None
    assert resp.response_type == "ANSWER"
    assert resp.triage_level == expected_triage
    assert resp.mode == "model"
    assert len(resp.sections.guidelines_say) > 0
    assert len(resp.citations) > 0


# ---------------------------------------------------------------------------
# Test 4: Scorer-Detected Emergency Skips Generation
# ---------------------------------------------------------------------------
def test_scorer_detected_emergency_skips_generation(graph_deps: PipelineDeps) -> None:
    """If scorer evaluates level to EMERGENCY, pipeline skips retriever and generator."""
    # Query passes gate but triggers emergency in scorer
    exploding_generator = AnswerGenerator(
        settings=graph_deps.settings,
        chat_model=ExplodingChatModel(),
    )
    deps = PipelineDeps(
        gate=graph_deps.gate,
        engine=graph_deps.engine,
        profiles=graph_deps.profiles,
        watch_for=graph_deps.watch_for,
        retriever=graph_deps.retriever,
        generator=exploding_generator,
        settings=graph_deps.settings,
    )

    app = build_graph(deps)
    # Stridor / respiratory distress
    init_state = create_initial_state(raw_text="Patient has stridor and choking sensation")
    result_state = app.invoke(init_state)

    resp: PipelineResponse = result_state["response"]
    assert resp.response_type == "EMERGENCY"
    assert resp.triage_level == "EMERGENCY"
    assert resp.mode == "static"


# ---------------------------------------------------------------------------
# Test 5: Kill Switch: llm_enabled=False Produces Extractive Mode
# ---------------------------------------------------------------------------
def test_kill_switch_llm_enabled_false(graph_deps: PipelineDeps) -> None:
    """When llm_enabled is False, pipeline produces extractive answers without chat client."""
    mock_chat = MagicMock()
    disabled_settings = Settings(
        llm_enabled=False,
        retrieval_min_cosine=-1.0,
        retrieval_min_bm25=0.0,
    )
    generator = AnswerGenerator(settings=disabled_settings, chat_model=mock_chat)

    deps = PipelineDeps(
        gate=graph_deps.gate,
        engine=graph_deps.engine,
        profiles=graph_deps.profiles,
        watch_for=graph_deps.watch_for,
        retriever=graph_deps.retriever,
        generator=generator,
        settings=disabled_settings,
    )

    app = build_graph(deps)
    init_state = create_initial_state(raw_text="Watery diarrhea and cramps for 2 days")
    result_state = app.invoke(init_state)

    resp: PipelineResponse = result_state["response"]
    assert resp.response_type == "ANSWER"
    assert resp.mode == "extractive"
    mock_chat.invoke.assert_not_called()


# ---------------------------------------------------------------------------
# Test 6: Static Intercept Performance (< 50ms)
# ---------------------------------------------------------------------------
def test_static_intercept_performance_under_50ms(graph_deps: PipelineDeps) -> None:
    """Static safety responses must execute in under 50 milliseconds of graph time."""
    app = build_graph(graph_deps)
    query = "I have severe crushing chest pain radiating to my left shoulder and sweating"

    # Warm up run
    app.invoke(create_initial_state(raw_text=query))

    start = time.perf_counter()
    init_state = create_initial_state(raw_text=query)
    result_state = app.invoke(init_state)
    elapsed_ms = (time.perf_counter() - start) * 1000.0

    resp: PipelineResponse = result_state["response"]
    assert resp.response_type == "EMERGENCY"
    assert elapsed_ms < 50.0, f"Static intercept took {elapsed_ms:.2f} ms (expected < 50ms)"
