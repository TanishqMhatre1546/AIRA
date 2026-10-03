"""Comprehensive API endpoint and middleware integration tests for AIRA."""

import io
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.rate_limit import ModelCallBudget, SlidingWindowRateLimiter
from app.core.generator import AnswerGenerator
from app.core.graph import PipelineDeps, build_graph
from app.core.validators import Claim, Draft
from app.main import create_app


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


@asynccontextmanager
async def client_context(
    fake_model: Any = None,
    exploding_model: bool = False,
    budget_limit: int = 1000,
    rate_limit: int = 20,
) -> AsyncIterator[tuple[AsyncClient, FastAPI]]:
    """Context manager setting up test client and application with lifespan."""
    app = create_app()
    async with app.router.lifespan_context(app):
        model = ExplodingChatModel() if exploding_model else (fake_model or MockWorkingChatModel())
        if app.state.deps is not None:
            budget = ModelCallBudget(limit=budget_limit)
            app.state.budget = budget
            generator = AnswerGenerator(
                settings=app.state.deps.settings,
                chat_model=model,
                budget=budget,
            )
            deps = PipelineDeps(
                gate=app.state.deps.gate,
                engine=app.state.deps.engine,
                profiles=app.state.deps.profiles,
                watch_for=app.state.deps.watch_for,
                retriever=app.state.deps.retriever,
                generator=generator,
                settings=app.state.deps.settings,
                clock=app.state.deps.clock,
            )
            app.state.graph = build_graph(deps)
            app.state.deps = deps
            app.state.generator = generator

        app.state.rate_limiter = SlidingWindowRateLimiter(default_limit=rate_limit)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client, app


@pytest.mark.asyncio
async def test_health_endpoint() -> None:
    """GET /api/health returns 200 ok."""
    async with client_context() as (client, _app):
        resp = await client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_ready_endpoint() -> None:
    """GET /api/ready returns 200 ready when loaded."""
    async with client_context() as (client, _app):
        resp = await client.get("/api/ready")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ready"}


@pytest.mark.asyncio
async def test_not_ready_state_refuses_triage() -> None:
    """Not-ready state returns 503 on /api/ready and refuses /api/triage."""
    app = create_app()
    app.state.is_ready = False
    app.state.ready_reason = "CORRUPTED_INDEX_HASH"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        ready_resp = await ac.get("/api/ready")
        assert ready_resp.status_code == 503
        data = ready_resp.json()
        assert data["status"] == "not_ready"
        assert data["reason"] == "CORRUPTED_INDEX_HASH"

        triage_resp = await ac.post("/api/triage", json={"message": "mild headache"})
        assert triage_resp.status_code == 503
        assert "not ready" in triage_resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_severe_chest_pain_emergency_static_intercept() -> None:
    """severe chest pain returns EMERGENCY with helplines, static mode, zero model calls."""
    async with client_context(exploding_model=True) as (client, _app):
        raw_query = "severe chest pain"
        resp = await client.post("/api/triage", json={"message": raw_query})
        assert resp.status_code == 200
        data = resp.json()

        assert data["response_type"] == "EMERGENCY"
        assert data["triage_level"] == "EMERGENCY"
        assert data["mode"] == "static"
        assert len(data["helplines"]) > 0
        assert any(h["number"] == "112" for h in data["helplines"])
        assert "request_id" in data

        # The response never contains the original message text for static outcomes
        assert raw_query not in data["headline"]
        assert raw_query not in data["message"]
        assert raw_query not in data["disclaimer"]


@pytest.mark.asyncio
async def test_what_dose_of_paracetamol_refusal() -> None:
    """what dose of paracetamol returns REFUSAL."""
    async with client_context(exploding_model=True) as (client, _app):
        resp = await client.post(
            "/api/triage", json={"message": "what dose of paracetamol should I take"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["response_type"] == "REFUSAL"
        assert data["mode"] == "static"
        msg_lower = data["message"].lower()
        assert (
            "cannot give medication doses" in msg_lower
            or "cannot provide individual dosages" in msg_lower
        )


@pytest.mark.asyncio
async def test_mild_headache_returns_answer() -> None:
    """mild headache since yesterday returns ANSWER with SELF_CARE and at least one citation."""
    async with client_context() as (client, _app):
        resp = await client.post("/api/triage", json={"message": "mild headache since yesterday"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["response_type"] == "ANSWER"
        assert data["triage_level"] in ("SELF_CARE", "SEE_DOCTOR")
        assert len(data["citations"]) >= 1
        assert "disclaimer" in data


@pytest.mark.asyncio
async def test_input_validation_and_length_limits() -> None:
    """501 characters returns 422, under 2 chars returns 422."""
    async with client_context() as (client, _app):
        # 501 characters
        long_msg = "a" * 501
        resp = await client.post("/api/triage", json={"message": long_msg})
        assert resp.status_code == 422

        # Under 2 characters
        short_msg = "a"
        resp_short = await client.post("/api/triage", json={"message": short_msg})
        assert resp_short.status_code == 422

        # Empty after whitespace strip
        empty_msg = "   "
        resp_empty = await client.post("/api/triage", json={"message": empty_msg})
        assert resp_empty.status_code == 422


@pytest.mark.asyncio
async def test_rate_limiter_exceeded() -> None:
    """Rate limit returns 429 with Retry-After header."""
    async with client_context(rate_limit=2) as (client, _app):
        r1 = await client.post("/api/triage", json={"message": "mild headache"})
        assert r1.status_code == 200

        r2 = await client.post("/api/triage", json={"message": "mild headache"})
        assert r2.status_code == 200

        r3 = await client.post("/api/triage", json={"message": "mild headache"})
        assert r3.status_code == 429
        assert "Retry-After" in r3.headers
        assert int(r3.headers["Retry-After"]) >= 1


@pytest.mark.asyncio
async def test_metadata_endpoint() -> None:
    """GET /api/meta returns complete metadata and adheres to clinical review policy."""
    async with client_context() as (client, _app):
        resp = await client.get("/api/meta")
        assert resp.status_code == 200
        data = resp.json()

        assert data["version"] == "0.1.0"
        assert len(data["corpus_hash"]) == 64
        assert data["rule_table_version"] == "2.0.0"
        assert data["counts"]["conditions"] >= 15
        assert data["counts"]["chunks"] >= 80
        assert data["counts"]["rules"] >= 25
        assert len(data["supported_conditions"]) >= 15
        assert data["clinical_review_status"]["reviewed"] is False
        assert data["clinical_review_status"]["reviewer"] is None
        assert "AIRA provides general health information" in data["disclaimer"]


@pytest.mark.asyncio
async def test_sources_endpoint() -> None:
    """GET /api/sources returns authoritative source guidelines and supported conditions."""
    async with client_context() as (client, _app):
        resp = await client.get("/api/sources")
        assert resp.status_code == 200
        data = resp.json()
        assert "sources" in data
        sources = data["sources"]
        assert len(sources) > 0
        for src in sources:
            assert src["title"]
            assert src["publisher"]
            assert len(src["conditions"]) > 0


@pytest.mark.asyncio
async def test_body_size_limit() -> None:
    """Payloads exceeding 4 KB return 413 Payload Too Large."""
    async with client_context() as (client, _app):
        huge_payload = {"message": "mild headache " + ("x" * 5000)}
        resp = await client.post("/api/triage", json=huge_payload)
        assert resp.status_code == 413


@pytest.mark.asyncio
async def test_security_and_tracing_headers() -> None:
    """Valid X-Request-ID preserved, invalid replaced, security headers set."""
    async with client_context() as (client, _app):
        # Valid custom request ID
        custom_id = "test-custom-request-id-12345"
        resp = await client.get("/api/health", headers={"X-Request-ID": custom_id})
        assert resp.status_code == 200
        assert resp.headers.get("X-Request-ID") == custom_id
        assert resp.headers.get("X-Content-Type-Options") == "nosniff"
        assert resp.headers.get("Referrer-Policy") == "no-referrer"
        assert "default-src 'none'" in resp.headers.get("Content-Security-Policy", "")

        # Malformed request ID should be replaced with valid UUID
        malformed_id = "invalid<script>alert(1)</script>"
        resp_bad = await client.get("/api/health", headers={"X-Request-ID": malformed_id})
        assert resp_bad.status_code == 200
        new_id = resp_bad.headers.get("X-Request-ID")
        assert new_id != malformed_id
        assert len(new_id) >= 16


@pytest.mark.asyncio
async def test_model_call_budget_exhaustion_switches_to_extractive() -> None:
    """Exhausting daily model budget forces extractive fallback mode."""
    async with client_context(budget_limit=0) as (client, _app):
        resp = await client.post("/api/triage", json={"message": "mild headache since yesterday"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["response_type"] == "ANSWER"
        assert data["mode"] == "extractive"


@pytest.mark.asyncio
async def test_logs_captured_contain_no_user_message_text() -> None:
    """Logs captured during a request contain no message text (strict privacy invariant)."""
    log_capture = io.StringIO()
    handler = logging.StreamHandler(log_capture)
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)

    test_marker_string = "unusual_symptom_marker_998877"
    try:
        async with client_context() as (client, _app):
            resp = await client.post(
                "/api/triage", json={"message": f"mild headache and {test_marker_string}"}
            )
            assert resp.status_code == 200

            logged_content = log_capture.getvalue()
            assert test_marker_string not in logged_content
            assert "unusual_symptom_marker" not in logged_content
    finally:
        root_logger.removeHandler(handler)
