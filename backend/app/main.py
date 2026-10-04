"""Main entrypoint and FastAPI application factory for AIRA."""

import contextlib
import json
import logging
import time
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.middleware import (
    BodySizeLimitMiddleware,
    RequestIdMiddleware,
    SecurityHeadersMiddleware,
)
from app.api.rate_limit import ModelCallBudget, SlidingWindowRateLimiter
from app.api.routes import router
from app.config import Settings, settings
from app.core.generator import AnswerGenerator
from app.core.graph import PipelineDeps, build_graph
from app.core.helplines import get_crisis_helplines, get_emergency_helplines
from app.core.retriever import Retriever
from app.core.rule_engine import RuleEngine
from app.core.safety_gate import SafetyGate
from app.core.scorer import load_condition_profiles
from app.data.corpus_loader import (
    extract_watch_for_map,
    load_condition_documents,
    load_provenance_statuses,
)
from app.data.rules_loader import load_drug_lexicon_list, load_raw_rules
from app.logging_config import log_event, setup_logging

logger = logging.getLogger("aira.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifecycle context manager performing startup checks and dependency loading."""
    setup_logging(settings.log_level)

    # Initialize state defaults
    app.state.is_ready = False
    app.state.ready_reason = "INITIALIZING"
    app.state.rate_limiter = SlidingWindowRateLimiter(
        default_limit=settings.rate_limit_per_minute,
        window_seconds=60.0,
    )
    app.state.budget = ModelCallBudget(limit=settings.daily_model_call_budget)
    app.state.graph = None
    app.state.deps = None
    app.state.condition_docs = []
    app.state.chunks = []
    app.state.rules = []
    app.state.supported_conditions = []
    app.state.corpus_hash = "unknown"
    app.state.rule_table_version = "unknown"

    try:
        data_dir = settings.data_dir

        # 1. Load rules, lexicon, and safety gate
        rules = load_raw_rules(data_dir)
        drugs = load_drug_lexicon_list(data_dir)
        scorer_engine = RuleEngine(rules=rules, lexicon=drugs)
        gate = SafetyGate(scorer_engine)

        # 2. Load condition profiles
        profiles = load_condition_profiles(data_dir / "lexicon" / "condition_profiles.json")

        # 3. Load embedder if LLM is enabled and key is present
        embedder = None
        if (
            settings.llm_enabled
            and settings.gemini_api_key
            and settings.gemini_api_key.get_secret_value().strip()
        ):
            from langchain_google_genai import GoogleGenerativeAIEmbeddings

            embedder = GoogleGenerativeAIEmbeddings(  # type: ignore[call-arg]
                model=settings.embedding_model,
                google_api_key=settings.gemini_api_key.get_secret_value(),
            )

        # 4. Load retriever from index and validate manifest hashes
        retriever = Retriever.from_disk(
            index_dir=data_dir / "index",
            curated_dir=data_dir / "curated",
            embedder=embedder,
            settings=settings,
        )

        # 5. Extract watch-for danger items and build generator
        watch_for = extract_watch_for_map(retriever.chunks)
        generator = AnswerGenerator(
            settings=settings,
            budget=app.state.budget,
        )

        # 6. Load intake questions and verified item IDs
        provenance_file = data_dir / "curated" / "provenance.csv"
        verified_item_ids: set[str] = set()
        if provenance_file.exists():
            prov_statuses = load_provenance_statuses(provenance_file)
            verified_item_ids = {iid for iid, st in prov_statuses.items() if st == "verified"}

        intake_data = None
        intake_file = data_dir / "intake" / "intake_questions.json"
        if intake_file.exists():
            with open(intake_file, encoding="utf-8") as f:
                intake_data = json.load(f)
        elif settings.intake_enabled:
            raise FileNotFoundError(f"Intake questions file not found: {intake_file}")

        # 7. Assemble LangGraph orchestration pipeline
        deps = PipelineDeps(
            gate=gate,
            engine=scorer_engine,
            profiles=profiles,
            watch_for=watch_for,
            retriever=retriever,
            generator=generator,
            settings=settings,
            intake_data=intake_data,
            verified_item_ids=verified_item_ids,
            clock=time.perf_counter,
        )
        graph = build_graph(deps)

        # 7. Load condition documents for metadata and sources endpoints
        condition_docs = load_condition_documents(data_dir / "curated")

        # 8. Load manifest corpus hash and rules version
        corpus_hash = "unknown"
        curated_manifest_file = data_dir / "curated" / "manifest.json"
        if curated_manifest_file.exists():
            with open(curated_manifest_file, encoding="utf-8") as f:
                curated_manifest = json.load(f)
                corpus_hash = curated_manifest.get("overall_corpus_hash", "unknown")

        rules_version = "2.0.0"
        urgency_rules_file = data_dir / "curated" / "urgency_rules.json"
        if urgency_rules_file.exists():
            with open(urgency_rules_file, encoding="utf-8") as f:
                rules_data = json.load(f)
                meta_block = rules_data.get("meta", {})
                rules_version = meta_block.get("version", "2.0.0")

        # Save to app state
        app.state.graph = graph
        app.state.deps = deps
        app.state.retriever = retriever
        app.state.generator = generator
        app.state.rules = rules
        app.state.condition_docs = condition_docs
        app.state.chunks = retriever.chunks
        app.state.supported_conditions = sorted({doc.condition for doc in condition_docs})
        app.state.corpus_hash = corpus_hash
        app.state.rule_table_version = rules_version

        app.state.is_ready = True
        app.state.ready_reason = None
        logger.info("AIRA application startup completed successfully. System is READY.")
    except Exception as exc:
        app.state.is_ready = False
        app.state.ready_reason = f"STARTUP_FAILED: {exc.__class__.__name__}: {exc}"
        logger.error("AIRA application startup failed: %s", exc)

    yield


def create_app(custom_settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    app_settings = custom_settings or settings

    app = FastAPI(
        title="AIRA Clinical Guidelines API",
        description="Clinical guideline navigator for India",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Register Middlewares in proper execution order
    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )
    app.add_middleware(
        BodySizeLimitMiddleware,
        max_body_size=app_settings.max_request_body_bytes,
    )
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestIdMiddleware)

    # Register global uncaught exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        req_id = getattr(request.state, "request_id", None) or uuid.uuid4().hex
        emergency_helplines = get_emergency_helplines()
        crisis_helplines = get_crisis_helplines()
        helpline_items = [
            {"label": h.name, "number": h.number} for h in (emergency_helplines + crisis_helplines)
        ]
        with contextlib.suppress(Exception):
            log_event("http.unhandled_exception", request_id=req_id, status_code=500)

        return JSONResponse(
            status_code=500,
            content={
                "detail": "An unexpected error occurred while processing your request.",
                "request_id": req_id,
                "helplines": helpline_items,
            },
            headers={"X-Request-ID": req_id},
        )

    # Include API routes
    app.include_router(router)

    return app


app = create_app()
