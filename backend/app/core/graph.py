"""LangGraph StateGraph orchestration pipeline for AIRA clinical query flow."""

import contextlib
import time
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, Literal, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel, Field

from app.config import Settings
from app.core.generator import AnswerGenerator
from app.core.helplines import (
    get_emergency_helplines,
)
from app.core.retriever import RetrievalResult, Retriever
from app.core.rule_engine import RuleEngine
from app.core.safety_gate import GateDecision, SafetyGate
from app.core.scorer import ScoreResult, symptom_urgency_scorer
from app.core.text import normalize, tokens
from app.core.validators import Citation, GeneratedAnswer, ValidatedClaim
from app.logging_config import log_event

STANDARD_DISCLAIMER = (
    "AIRA provides general health information from standard Indian clinical guidelines "
    "(ICMR, MOHFW). It is not a doctor, cannot diagnose, and cannot prescribe medicines. "
    "In an emergency, call 112 immediately."
)

SUPPORTED_CONDITIONS_LIST = (
    "Acute Diarrhea, Acute Respiratory Infections, Acute Rhinosinusitis, "
    "Bacterial Skin Infections, Dengue Fever, Dermatophytosis (Ringworm), "
    "Type 2 Diabetes, Eczema / Dermatitis, Epistaxis (Nosebleed), "
    "Headache, Hypertension, Pharyngitis (Sore Throat), Scabies, "
    "Urinary Tract Infection, Urticaria / Angioedema."
)


class HelplineItem(BaseModel):
    """Emergency or crisis helpline reference."""

    label: str
    number: str


class ResponseSections(BaseModel):
    """Structured clinical summary sections."""

    guidelines_say: list[ValidatedClaim] = Field(default_factory=list)
    do_now: list[ValidatedClaim] = Field(default_factory=list)
    watch_for: list[ValidatedClaim] = Field(default_factory=list)


class PipelineResponse(BaseModel):
    """Top-level immutable clinical response object for AIRA pipeline."""

    response_type: Literal["EMERGENCY", "CRISIS", "REFUSAL", "OUT_OF_SCOPE", "NO_MATCH", "ANSWER"]
    triage_level: Literal["EMERGENCY", "SEE_DOCTOR", "SELF_CARE", "UNKNOWN"] | None = None
    headline: str
    message: str
    helplines: list[HelplineItem] = Field(default_factory=list)
    sections: ResponseSections = Field(default_factory=ResponseSections)
    citations: list[Citation] = Field(default_factory=list)
    mode: Literal["static", "model", "extractive"]
    disclaimer: str = STANDARD_DISCLAIMER


class PipelineState(TypedDict):
    """LangGraph execution state passed through pipeline nodes."""

    request_id: str
    raw_text: str
    norm_tokens: list[str]
    gate: GateDecision | None
    score: ScoreResult | None
    retrieval: RetrievalResult | None
    draft: GeneratedAnswer | None
    response: PipelineResponse | None
    timings: dict[str, float]


@dataclass
class PipelineDeps:
    """Dependency container injected into the compiled LangGraph pipeline."""

    gate: SafetyGate
    engine: RuleEngine
    profiles: dict[str, Any]
    watch_for: Mapping[str, list[str]]
    retriever: Retriever
    generator: AnswerGenerator
    settings: Settings
    clock: Callable[[], float] = time.perf_counter


def create_initial_state(raw_text: str, request_id: str | None = None) -> PipelineState:
    """Helper to initialize a clean PipelineState dict."""
    return {
        "request_id": request_id or str(uuid.uuid4()),
        "raw_text": raw_text,
        "norm_tokens": [],
        "gate": None,
        "score": None,
        "retrieval": None,
        "draft": None,
        "response": None,
        "timings": {},
    }


def build_graph(deps: PipelineDeps) -> CompiledStateGraph[Any, Any, Any, Any]:
    """Assemble and compile the deterministic LangGraph pipeline with strict safety routing."""

    def wrap_node(
        node_name: str,
        node_func: Callable[[PipelineState], dict[str, Any]],
    ) -> Any:
        """Wrap node execution to record timings and structured log events."""

        def wrapped(state: PipelineState) -> dict[str, Any]:
            t0 = deps.clock()
            patch = node_func(state)
            elapsed_ms = (deps.clock() - t0) * 1000.0

            curr_timings = dict(state.get("timings") or {})
            curr_timings[node_name] = round(elapsed_ms, 2)
            patch["timings"] = curr_timings

            # Log node event
            resp = patch.get("response") or state.get("response")
            resp_type = resp.response_type if resp else None
            score_obj = patch.get("score") or state.get("score")
            triage = (
                resp.triage_level
                if resp and resp.triage_level
                else (score_obj.level if score_obj is not None else None)
            )
            gate_dec = patch.get("gate") or state.get("gate")
            rule_id = gate_dec.rule_id if gate_dec else None
            mode_val = resp.mode if resp else None

            log_kwargs: dict[str, Any] = {
                "node": node_name,
                "elapsed_ms": round(elapsed_ms, 2),
            }
            if state.get("request_id"):
                log_kwargs["request_id"] = state["request_id"]
            if resp_type:
                log_kwargs["response_type"] = resp_type
            if triage:
                log_kwargs["triage_level"] = triage
            if rule_id:
                log_kwargs["rule_id"] = rule_id
            if mode_val:
                log_kwargs["mode"] = mode_val

            with contextlib.suppress(Exception):
                log_event(f"node.{node_name}", **log_kwargs)

            return patch

        return wrapped

    # 1. Node implementations
    def node_normalize(state: PipelineState) -> dict[str, Any]:
        norm = normalize(state["raw_text"])
        toks = tokens(norm)
        return {"norm_tokens": toks}

    def node_gate(state: PipelineState) -> dict[str, Any]:
        decision = deps.gate.evaluate_safe(state["raw_text"])
        return {"gate": decision}

    def node_respond_static(state: PipelineState) -> dict[str, Any]:
        gate_dec = state.get("gate")
        score_res = state.get("score")

        if gate_dec and gate_dec.outcome != "PASS":
            outcome = gate_dec.outcome
            rule_msg = gate_dec.message or ""
            helpline_items = [
                HelplineItem(label=h.name, number=h.number) for h in gate_dec.helplines
            ]

            if outcome == "EMERGENCY":
                headline = "Immediate Emergency Medical Attention Required"
                msg = (
                    rule_msg
                    or "Emergency symptoms detected. "
                    "Please seek emergency medical care immediately."
                )
                triage_val: Literal["EMERGENCY", "SEE_DOCTOR", "SELF_CARE", "UNKNOWN"] | None = (
                    "EMERGENCY"
                )
            elif outcome == "CRISIS":
                headline = "Mental Health and Crisis Support"
                msg = (
                    rule_msg
                    or "If you are in distress or experiencing thoughts of self-harm, "
                    "support is available 24/7."
                )
                triage_val = None
            elif outcome == "REFUSAL":
                headline = "Medical Safety Guidance"
                msg = (
                    rule_msg
                    or "AIRA cannot provide individual dosages, diagnostic confirmations, "
                    "or advise on combining medications."
                )
                triage_val = None
            else:  # OUT_OF_SCOPE
                headline = "Topic Beyond AIRA Adult Care Scope"
                msg = (
                    rule_msg
                    or "This query is outside AIRA's current scope for non-emergency "
                    "adult health guidance."
                )
                triage_val = None

            resp = PipelineResponse(
                response_type=outcome,
                triage_level=triage_val,
                headline=headline,
                message=msg,
                helplines=helpline_items,
                sections=ResponseSections(),
                citations=[],
                mode="static",
                disclaimer=STANDARD_DISCLAIMER,
            )
            return {"response": resp}

        if score_res and score_res.level == "EMERGENCY":
            emergency_helplines = [
                HelplineItem(label=h.name, number=h.number) for h in get_emergency_helplines()
            ]
            watch_claims = [ValidatedClaim(text=w, citation_ids=[]) for w in score_res.watch_for]
            msg = (
                score_res.urgency_note
                or "Emergency symptoms detected. Please seek emergency medical care immediately."
            )
            resp = PipelineResponse(
                response_type="EMERGENCY",
                triage_level="EMERGENCY",
                headline="Immediate Emergency Medical Attention Required",
                message=msg,
                helplines=emergency_helplines,
                sections=ResponseSections(watch_for=watch_claims),
                citations=[],
                mode="static",
                disclaimer=STANDARD_DISCLAIMER,
            )
            return {"response": resp}

        # Fallback safe emergency response
        resp = PipelineResponse(
            response_type="EMERGENCY",
            triage_level="EMERGENCY",
            headline="Immediate Emergency Medical Attention Required",
            message="Please seek emergency medical care immediately.",
            helplines=[
                HelplineItem(label=h.name, number=h.number) for h in get_emergency_helplines()
            ],
            sections=ResponseSections(),
            citations=[],
            mode="static",
            disclaimer=STANDARD_DISCLAIMER,
        )
        return {"response": resp}

    def node_score(state: PipelineState) -> dict[str, Any]:
        score_res = symptom_urgency_scorer(
            symptoms=state["raw_text"],
            engine=deps.engine,
            profiles=deps.profiles,
            watch_for=deps.watch_for,
        )
        return {"score": score_res}

    def node_retrieve(state: PipelineState) -> dict[str, Any]:
        score_state = state.get("score")
        detected_conditions = score_state.conditions if score_state is not None else []
        retrieval_res = deps.retriever.search(
            query=state["raw_text"],
            conditions=detected_conditions,
            top_k=deps.settings.top_k,
        )
        return {"retrieval": retrieval_res}

    def node_respond_no_match(state: PipelineState) -> dict[str, Any]:
        msg = (
            "AIRA covers common primary care conditions based on Indian clinical guidelines. "
            "You can view all supported conditions on our Sources page: "
            f"{SUPPORTED_CONDITIONS_LIST}"
        )
        resp = PipelineResponse(
            response_type="NO_MATCH",
            triage_level=None,
            headline="Condition Not Covered in Current Guidelines",
            message=msg,
            helplines=[],
            sections=ResponseSections(),
            citations=[],
            mode="static",
            disclaimer=STANDARD_DISCLAIMER,
        )
        return {"response": resp}

    def node_generate(state: PipelineState) -> dict[str, Any]:
        retrieval = state.get("retrieval")
        chunks = [sc.chunk for sc in retrieval.chunks] if retrieval else []
        draft = deps.generator.generate(query=state["raw_text"], chunks=chunks)
        return {"draft": draft}

    def node_respond_answer(state: PipelineState) -> dict[str, Any]:
        score_res = state.get("score")
        draft = state.get("draft")

        triage_val = score_res.level if score_res else "UNKNOWN"
        if triage_val == "SEE_DOCTOR":
            headline = "Medical Consultation Recommended"
        elif triage_val == "SELF_CARE":
            headline = "Guideline Self-Care Advice"
        else:
            headline = "Clinical Guideline Information"

        msg = (
            score_res.urgency_note if score_res else None
        ) or "Guideline recommendations for your reported symptoms."

        watch_claims = (
            [ValidatedClaim(text=w, citation_ids=[]) for w in score_res.watch_for]
            if score_res
            else []
        )
        g_say = draft.guidelines_say if draft else []
        d_now = draft.do_now if draft else []
        cits = draft.citations if draft else []
        ans_mode = draft.mode if draft else "extractive"

        triage_literal: Literal["EMERGENCY", "SEE_DOCTOR", "SELF_CARE", "UNKNOWN"] | None = (
            triage_val
            if triage_val in ("EMERGENCY", "SEE_DOCTOR", "SELF_CARE", "UNKNOWN")
            else "UNKNOWN"  # type: ignore[assignment]
        )

        resp = PipelineResponse(
            response_type="ANSWER",
            triage_level=triage_literal,
            headline=headline,
            message=msg,
            helplines=[],
            sections=ResponseSections(
                guidelines_say=g_say,
                do_now=d_now,
                watch_for=watch_claims,
            ),
            citations=cits,
            mode=ans_mode,
            disclaimer=STANDARD_DISCLAIMER,
        )
        return {"response": resp}

    # 2. Build workflow graph
    workflow = StateGraph(PipelineState)

    workflow.add_node("normalize", wrap_node("normalize", node_normalize))
    workflow.add_node("gate", wrap_node("gate", node_gate))
    workflow.add_node("respond_static", wrap_node("respond_static", node_respond_static))
    workflow.add_node("score", wrap_node("score", node_score))
    workflow.add_node("retrieve", wrap_node("retrieve", node_retrieve))
    workflow.add_node("respond_no_match", wrap_node("respond_no_match", node_respond_no_match))
    workflow.add_node("generate", wrap_node("generate", node_generate))
    workflow.add_node("respond_answer", wrap_node("respond_answer", node_respond_answer))

    # Edges
    workflow.add_edge(START, "normalize")
    workflow.add_edge("normalize", "gate")

    # Conditional routing from gate
    def route_gate(state: PipelineState) -> Literal["respond_static", "score"]:
        gate_dec = state.get("gate")
        if gate_dec and gate_dec.outcome != "PASS":
            return "respond_static"
        return "score"

    workflow.add_conditional_edges(
        "gate",
        route_gate,
        {"respond_static": "respond_static", "score": "score"},
    )

    # Conditional routing from score
    def route_score(state: PipelineState) -> Literal["respond_static", "retrieve"]:
        score_res = state.get("score")
        if score_res and score_res.level == "EMERGENCY":
            return "respond_static"
        return "retrieve"

    workflow.add_conditional_edges(
        "score",
        route_score,
        {"respond_static": "respond_static", "retrieve": "retrieve"},
    )

    # Conditional routing from retrieve
    def route_retrieve(state: PipelineState) -> Literal["respond_no_match", "generate"]:
        retrieval = state.get("retrieval")
        if not retrieval or not retrieval.chunks:
            return "respond_no_match"
        return "generate"

    workflow.add_conditional_edges(
        "retrieve",
        route_retrieve,
        {"respond_no_match": "respond_no_match", "generate": "generate"},
    )

    workflow.add_edge("generate", "respond_answer")

    workflow.add_edge("respond_static", END)
    workflow.add_edge("respond_no_match", END)
    workflow.add_edge("respond_answer", END)

    return workflow.compile()
