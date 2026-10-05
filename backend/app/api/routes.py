"""API route handlers for user queries, system health, and guideline metadata."""

import uuid
from typing import Any, Literal

from fastapi import APIRouter, Request, Response, status
from fastapi.responses import JSONResponse

from app.api.rate_limit import SlidingWindowRateLimiter, get_client_ip
from app.api.schemas import (
    ClinicalReviewStatus,
    CountsMeta,
    HealthResponse,
    MetaResponse,
    NotReadyResponse,
    ReadyResponse,
    SourceItem,
    SourcesResponse,
    TriageRequest,
    TriageResponse,
)
from app.config import settings
from app.core.graph import STANDARD_DISCLAIMER, PipelineResponse, create_initial_state
from app.logging_config import log_event

router = APIRouter(prefix="/api", tags=["aira"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Liveness check",
    description="Always returns 200 to indicate process liveness.",
)
async def health_check() -> HealthResponse:
    """Liveness probe endpoint."""
    return HealthResponse(status="ok")


@router.get(
    "/ready",
    response_model=ReadyResponse,
    responses={
        200: {"model": ReadyResponse, "description": "Application dependencies ready"},
        503: {"model": NotReadyResponse, "description": "Application dependencies not ready"},
    },
    summary="Readiness check",
    description="Returns 200 when all rules, corpus, index, and models are loaded.",
)
async def readiness_check(request: Request) -> Response:
    """Readiness probe endpoint verifying all components are operational."""
    is_ready = getattr(request.app.state, "is_ready", False)
    if not is_ready:
        reason = getattr(request.app.state, "ready_reason", "NOT_INITIALIZED")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "reason": reason},
        )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "ready"},
    )


@router.post(
    "/triage",
    response_model=TriageResponse,
    responses={
        200: {"model": TriageResponse, "description": "Successful clinical triage evaluation"},
        413: {"description": "Payload body size exceeds 4 KB"},
        422: {"description": "Validation error for message format or length"},
        429: {"description": "Rate limit exceeded"},
        503: {"model": NotReadyResponse, "description": "Application is not ready"},
    },
    summary="Evaluate symptoms and provide guideline-backed guidance",
)
async def triage_symptoms(
    body: TriageRequest,
    request: Request,
) -> Response:
    """Process user symptom queries through the deterministic safety and guideline pipeline."""
    # 1. Check readiness
    is_ready = getattr(request.app.state, "is_ready", False)
    if not is_ready or not getattr(request.app.state, "graph", None):
        reason = getattr(request.app.state, "ready_reason", "SYSTEM_NOT_READY")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": "Service is not ready to process triage requests", "reason": reason},
        )

    # 2. Rate limiting check per client IP
    client_ip = get_client_ip(request)
    limiter: SlidingWindowRateLimiter | None = getattr(request.app.state, "rate_limiter", None)
    if limiter is not None:
        allowed, retry_after = limiter.check_rate_limit(client_ip)
        if not allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Too many requests. Please try again later."},
                headers={"Retry-After": str(retry_after)},
            )

    # 3. Request identification
    req_id = getattr(request.state, "request_id", None) or uuid.uuid4().hex

    # 4. Intake validation if intake payload provided
    deps = getattr(request.app.state, "deps", None)
    if body.intake and deps and deps.intake_data:
        from app.core.intake import validate_intake_payload

        try:
            validate_intake_payload(body.intake.model_dump(), deps.intake_data)
        except ValueError as exc:
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                content={"detail": str(exc)},
            )

    # 5. Execute pipeline graph
    initial_state = create_initial_state(
        raw_text=body.message,
        request_id=req_id,
        skip_intake=body.skip_intake,
        intake=body.intake.model_dump() if body.intake else None,
    )
    graph = request.app.state.graph
    final_state = await graph.ainvoke(initial_state)

    pipeline_resp: PipelineResponse = final_state["response"]

    # 6. Log structured completion event (booleans and counts only for intake telemetry)
    intake_shown = pipeline_resp.response_type == "FOLLOW_UP"
    intake_skipped = bool(body.skip_intake)
    intake_q_count = len(pipeline_resp.questions) if pipeline_resp.questions else 0

    draft_obj = final_state.get("draft")
    dropped_claims_val = draft_obj.dropped_claims if draft_obj else 0
    llm_err_val = draft_obj.llm_error if draft_obj else None

    log_kwargs: dict[str, Any] = {
        "request_id": req_id,
        "response_type": pipeline_resp.response_type,
        "triage_level": pipeline_resp.triage_level,
        "mode": pipeline_resp.mode,
        "status_code": 200,
        "intake_shown": intake_shown,
        "intake_skipped": intake_skipped,
        "intake_questions_count": intake_q_count,
        "dropped_claims": dropped_claims_val,
    }
    if llm_err_val:
        log_kwargs["llm_error"] = llm_err_val

    log_event("http.triage", **log_kwargs)

    triage_response = TriageResponse.from_pipeline_response(pipeline_resp, request_id=req_id)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=triage_response.model_dump(),
        headers={"X-Request-ID": req_id},
    )


@router.get(
    "/meta",
    response_model=MetaResponse,
    summary="Corpus, rule, and clinical review metadata",
)
async def get_metadata(request: Request) -> MetaResponse:
    """Retrieve corpus, rules, and system metadata."""
    corpus_hash = getattr(request.app.state, "corpus_hash", "unknown")
    rule_table_version = getattr(request.app.state, "rule_table_version", "2.0.0")
    condition_docs = getattr(request.app.state, "condition_docs", [])
    chunks = getattr(request.app.state, "chunks", [])
    rules = getattr(request.app.state, "rules", [])
    supported_conditions = getattr(request.app.state, "supported_conditions", [])

    # Strict review policy: never claim clinical review unless settings say so
    review_done = bool(settings.clinical_review_done)
    reviewer = settings.clinical_review_by if review_done else None
    review_date = settings.clinical_review_date if review_done else None

    cv_raw = getattr(request.app.state, "content_verification", "verified")
    content_verification: Literal["verified", "unverified"] = (
        "unverified" if cv_raw == "unverified" else "verified"
    )

    generator = getattr(request.app.state, "generator", None)
    llm_available = bool(getattr(generator, "llm_available", False)) if generator else False

    return MetaResponse(
        version="0.1.0",
        corpus_hash=corpus_hash,
        rule_table_version=rule_table_version,
        counts=CountsMeta(
            conditions=len(condition_docs),
            chunks=len(chunks),
            rules=len(rules),
        ),
        supported_conditions=supported_conditions,
        clinical_review_status=ClinicalReviewStatus(
            reviewed=review_done,
            reviewer=reviewer,
            date=review_date,
        ),
        disclaimer=STANDARD_DISCLAIMER,
        content_verification=content_verification,
        llm_available=llm_available,
    )


@router.get(
    "/sources",
    response_model=SourcesResponse,
    summary="Listing of authoritative clinical sources",
)
async def get_sources(request: Request) -> SourcesResponse:
    """Retrieve all authoritative guideline sources with the conditions they support."""
    condition_docs = getattr(request.app.state, "condition_docs", [])

    sources_map: dict[tuple[str, str, str | int | None, str | None], list[str]] = {}
    for doc in condition_docs:
        src = getattr(doc, "source", None)
        if src:
            key = (src.title, src.publisher, src.edition_year, src.url)
            if key not in sources_map:
                sources_map[key] = []
            if doc.condition not in sources_map[key]:
                sources_map[key].append(doc.condition)

    sources_list = [
        SourceItem(
            title=k[0],
            publisher=k[1],
            edition_year=k[2],
            url=k[3],
            conditions=sorted(conds),
        )
        for k, conds in sources_map.items()
    ]

    return SourcesResponse(sources=sources_list)
