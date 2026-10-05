"""LangGraph StateGraph orchestration pipeline for AIRA clinical query flow."""

import contextlib
import time
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any, Literal, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel, Field

from app.config import Settings
from app.core.generator import AnswerGenerator
from app.core.helplines import (
    get_emergency_helplines,
)
from app.core.intake import (
    parse_intake_answers,
    select_intake_questions,
    strip_question_for_client,
    validate_intake_payload,
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

SEVERITY_ORDER: dict[str, int] = {
    "UNKNOWN": 0,
    "SELF_CARE": 1,
    "SEE_DOCTOR": 2,
    "EMERGENCY": 3,
}


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

    response_type: Literal[
        "EMERGENCY", "CRISIS", "REFUSAL", "OUT_OF_SCOPE", "NO_MATCH", "ANSWER", "FOLLOW_UP"
    ]
    triage_level: Literal["EMERGENCY", "SEE_DOCTOR", "SELF_CARE", "UNKNOWN"] | None = None
    headline: str
    message: str
    helplines: list[HelplineItem] = Field(default_factory=list)
    sections: ResponseSections = Field(default_factory=ResponseSections)
    citations: list[Citation] = Field(default_factory=list)
    mode: Literal["static", "model", "extractive"]
    disclaimer: str = STANDARD_DISCLAIMER
    questions: list[dict[str, Any]] = Field(default_factory=list)
    allow_text: bool = False
    text_max: int = 300
    skip_allowed: bool = False
    answers_summary: list[str] = Field(default_factory=list)


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
    # Intake workflow fields
    skip_intake: bool
    intake: dict[str, Any] | None
    augmented_text: str | None
    structured_duration: int | None
    structured_modifiers: list[str] | None
    forced_conditions: list[str] | None
    selected_option_ids: list[str] | None
    answers_summary: list[str] | None
    intake_questions: list[dict[str, Any]] | None


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
    intake_data: dict[str, Any] | None = None
    verified_item_ids: set[str] = field(default_factory=set)
    clock: Callable[[], float] = time.perf_counter


def create_initial_state(
    raw_text: str,
    request_id: str | None = None,
    skip_intake: bool = False,
    intake: dict[str, Any] | None = None,
) -> PipelineState:
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
        "skip_intake": skip_intake,
        "intake": intake,
        "augmented_text": None,
        "structured_duration": None,
        "structured_modifiers": None,
        "forced_conditions": None,
        "selected_option_ids": None,
        "answers_summary": None,
        "intake_questions": None,
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
            draft_obj = patch.get("draft") or state.get("draft")
            if draft_obj:
                log_kwargs["dropped_claims"] = draft_obj.dropped_claims
                if draft_obj.llm_error:
                    log_kwargs["llm_error"] = draft_obj.llm_error

            with contextlib.suppress(Exception):
                log_event(f"node.{node_name}", **log_kwargs)

            return patch

        return wrapped

    # 1. Node implementations
    def node_apply_intake(state: PipelineState) -> dict[str, Any]:
        intake = state.get("intake")
        if not intake or deps.intake_data is None:
            return {}

        validate_intake_payload(intake, deps.intake_data)
        parsed = parse_intake_answers(intake, deps.intake_data)

        # Format augmented text: "<message>. <extra_text>. <phrases...>"
        parts = [state["raw_text"].strip()]
        if parsed.get("extra_text"):
            parts.append(parsed["extra_text"])
        for phrase in parsed.get("canonical_phrases", []):
            if phrase.strip():
                parts.append(phrase.strip())

        augmented_text = ". ".join(parts)
        return {
            "augmented_text": augmented_text,
            "structured_duration": parsed.get("structured_duration"),
            "structured_modifiers": parsed.get("structured_modifiers"),
            "forced_conditions": parsed.get("forced_conditions"),
            "selected_option_ids": parsed.get("selected_option_ids"),
            "answers_summary": parsed.get("answers_summary"),
        }

    def node_normalize(state: PipelineState) -> dict[str, Any]:
        text_to_norm = state.get("augmented_text") or state["raw_text"]
        norm = normalize(text_to_norm)
        toks = tokens(norm)
        return {"norm_tokens": toks}

    def node_gate(state: PipelineState) -> dict[str, Any]:
        text_to_evaluate = state.get("augmented_text") or state["raw_text"]
        decision = deps.gate.evaluate_safe(text_to_evaluate)
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
        raw_text = state["raw_text"]
        aug_text = state.get("augmented_text")

        base_res = symptom_urgency_scorer(
            symptoms=raw_text,
            engine=deps.engine,
            profiles=deps.profiles,
            watch_for=deps.watch_for,
        )

        has_intake_signals = (
            bool(aug_text)
            or state.get("structured_duration") is not None
            or bool(state.get("structured_modifiers"))
            or bool(state.get("forced_conditions"))
            or bool(state.get("selected_option_ids"))
        )

        if not has_intake_signals:
            return {"score": base_res}

        aug_res = symptom_urgency_scorer(
            symptoms=aug_text or raw_text,
            engine=deps.engine,
            profiles=deps.profiles,
            watch_for=deps.watch_for,
            structured_duration=state.get("structured_duration"),
            structured_modifiers=state.get("structured_modifiers"),
            forced_conditions=state.get("forced_conditions"),
            intake_option_ids=state.get("selected_option_ids"),
        )

        base_rank = SEVERITY_ORDER.get(base_res.level, 0)
        aug_rank = SEVERITY_ORDER.get(aug_res.level, 0)

        # Monotonicity: answers can only escalate urgency, never lower it
        final_res = base_res if aug_rank < base_rank else aug_res

        return {"score": final_res}

    def node_intake_plan(state: PipelineState) -> dict[str, Any]:
        if deps.intake_data is None:
            return {"intake_questions": []}

        score_res = state.get("score")
        questions = select_intake_questions(
            score=score_res,
            raw_text=state["raw_text"],
            intake_data=deps.intake_data,
            allow_unverified=deps.settings.allow_unverified_content,
            verified_item_ids=deps.verified_item_ids,
            profiles=deps.profiles,
        )
        return {"intake_questions": questions}

    def node_respond_followup(state: PipelineState) -> dict[str, Any]:
        raw_questions = state.get("intake_questions") or []
        client_questions = [strip_question_for_client(q) for q in raw_questions]

        resp = PipelineResponse(
            response_type="FOLLOW_UP",
            triage_level=None,
            headline="A few quick questions",
            message=(
                "Answer these to help us check the right guideline sections, "
                "or skip to see your results."
            ),
            helplines=[],
            sections=ResponseSections(),
            citations=[],
            mode="static",
            disclaimer=STANDARD_DISCLAIMER,
            questions=client_questions,
            allow_text=True,
            text_max=300,
            skip_allowed=True,
            answers_summary=[],
        )
        return {"response": resp}

    def node_retrieve(state: PipelineState) -> dict[str, Any]:
        score_state = state.get("score")
        detected_conditions = score_state.conditions if score_state is not None else []
        query_text = state.get("augmented_text") or state["raw_text"]
        retrieval_res = deps.retriever.search(
            query=query_text,
            conditions=detected_conditions,
            top_k=deps.settings.top_k,
        )
        return {"retrieval": retrieval_res}

    def node_respond_no_match(state: PipelineState) -> dict[str, Any]:
        msg = (
            "AIRA could not match this to its guidelines. If you are worried, see a doctor.\n\n"
            f"Covered conditions: {SUPPORTED_CONDITIONS_LIST}"
        )
        resp = PipelineResponse(
            response_type="NO_MATCH",
            triage_level="UNKNOWN",
            headline="Not enough to decide",
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
        score_state = state.get("score")
        triage_level = score_state.level if score_state else "UNKNOWN"
        detected_conditions = score_state.conditions if score_state else []
        query_text = state.get("augmented_text") or state["raw_text"]
        model_chunks = chunks
        if triage_level != "EMERGENCY":
            non_danger = [
                ch for ch in chunks if ch.section_type not in ("danger_signs", "refer_urgently")
            ]
            if non_danger:
                model_chunks = non_danger

        draft = deps.generator.generate(
            query=query_text,
            chunks=model_chunks,
            triage_level=triage_level,
            detected_conditions=detected_conditions,
            all_chunks=deps.retriever.chunks,
        )
        return {"draft": draft}

    def node_respond_answer(state: PipelineState) -> dict[str, Any]:
        score_res = state.get("score")
        draft = state.get("draft")

        triage_val = score_res.level if score_res else "UNKNOWN"
        detected_conditions = score_res.conditions if score_res else []

        if triage_val == "SEE_DOCTOR":
            headline = "Medical Consultation Recommended"
        elif triage_val == "SELF_CARE":
            headline = "Guideline Self-Care Advice"
        elif triage_val == "EMERGENCY":
            headline = "Immediate Emergency Medical Attention Required"
        else:
            headline = "Not enough to decide"

        msg = (
            score_res.urgency_note if score_res else None
        ) or (
            "AIRA could not match this to its guidelines. If you are worried, see a doctor."
            if triage_val == "UNKNOWN"
            else "Guideline recommendations for your reported symptoms."
        )

        draft_cits = draft.citations if draft else []
        citation_map: dict[tuple[str, int | None], Citation] = {
            (c.title, c.page): c for c in draft_cits
        }
        next_cit_id = max([c.id for c in draft_cits], default=0) + 1

        watch_claims: list[ValidatedClaim] = []
        if detected_conditions and triage_val != "UNKNOWN":
            from app.core.validators import extract_items_from_chunk
            from app.data.corpus_loader import to_corpus_condition_id, to_profile_condition_id

            target_cids = set()
            for cid in detected_conditions:
                target_cids.add(cid)
                target_cids.add(to_corpus_condition_id(cid))
                target_cids.add(to_profile_condition_id(cid))

            danger_chunks = [
                ch
                for ch in deps.retriever.chunks
                if ch.condition_id in target_cids
                and ch.section_type in ("danger_signs", "refer_urgently")
            ]

            collected_watch_items: list[tuple[str, Any]] = []
            for ch in danger_chunks:
                items = extract_items_from_chunk(ch)
                for itm in items:
                    if len(itm) > 220:
                        itm = itm[:217] + "..."
                    collected_watch_items.append((itm, ch))
                    if len(collected_watch_items) >= 5:
                        break
                if len(collected_watch_items) >= 5:
                    break

            for text_str, ch in collected_watch_items:
                key = (ch.source_title, ch.page)
                if key not in citation_map:
                    cit = Citation(
                        id=next_cit_id,
                        title=ch.source_title,
                        publisher=ch.source_publisher,
                        year=str(ch.source_year),
                        page=ch.page,
                        url=ch.source_url,
                    )
                    citation_map[key] = cit
                    cit_id = next_cit_id
                    next_cit_id += 1
                else:
                    cit_id = citation_map[key].id
                watch_claims.append(ValidatedClaim(text=text_str, citation_ids=[cit_id]))

        all_citations = sorted(citation_map.values(), key=lambda c: c.id)

        g_say = draft.guidelines_say if draft else []
        d_now = draft.do_now if draft else []
        ans_mode = draft.mode if draft else "extractive"
        summary_items = state.get("answers_summary") or []

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
            citations=all_citations,
            mode=ans_mode,
            disclaimer=STANDARD_DISCLAIMER,
            answers_summary=summary_items,
        )
        return {"response": resp}

    def should_do_intake(state: PipelineState) -> bool:
        """Check if the query qualifies for Round 1 guided intake questions."""
        if not deps.settings.intake_enabled:
            return False
        if deps.intake_data is None:
            return False
        if state.get("skip_intake", False):
            return False
        intake = state.get("intake")
        if intake and (intake.get("answers") or intake.get("extra_text")):
            return False
        score_res = state.get("score")
        if score_res and score_res.level == "EMERGENCY":
            return False
        gate_dec = state.get("gate")
        return not (gate_dec and gate_dec.outcome != "PASS")

    # 2. Build workflow graph
    workflow = StateGraph(PipelineState)

    workflow.add_node("apply_intake", wrap_node("apply_intake", node_apply_intake))
    workflow.add_node("normalize", wrap_node("normalize", node_normalize))
    workflow.add_node("gate", wrap_node("gate", node_gate))
    workflow.add_node("respond_static", wrap_node("respond_static", node_respond_static))
    workflow.add_node("score", wrap_node("score", node_score))
    workflow.add_node("intake_plan", wrap_node("intake_plan", node_intake_plan))
    workflow.add_node("respond_followup", wrap_node("respond_followup", node_respond_followup))
    workflow.add_node("retrieve", wrap_node("retrieve", node_retrieve))
    workflow.add_node("respond_no_match", wrap_node("respond_no_match", node_respond_no_match))
    workflow.add_node("generate", wrap_node("generate", node_generate))
    workflow.add_node("respond_answer", wrap_node("respond_answer", node_respond_answer))

    # Edges
    workflow.add_edge(START, "apply_intake")
    workflow.add_edge("apply_intake", "normalize")
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
    def route_score(state: PipelineState) -> Literal["respond_static", "intake_plan", "retrieve"]:
        score_res = state.get("score")
        if score_res and score_res.level == "EMERGENCY":
            return "respond_static"
        if should_do_intake(state):
            return "intake_plan"
        return "retrieve"

    workflow.add_conditional_edges(
        "score",
        route_score,
        {
            "respond_static": "respond_static",
            "intake_plan": "intake_plan",
            "retrieve": "retrieve",
        },
    )

    workflow.add_edge("intake_plan", "respond_followup")
    workflow.add_edge("respond_followup", END)

    # Conditional routing from retrieve
    def route_retrieve(state: PipelineState) -> Literal["respond_no_match", "generate"]:
        score_state = state.get("score")
        detected_conditions = score_state.conditions if score_state is not None else []
        if not detected_conditions:
            return "respond_no_match"
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
