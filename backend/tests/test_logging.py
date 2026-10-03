"""Unit tests for structured logging and privacy invariant enforcement."""

import json
import logging

import pytest

from app.logging_config import JSONFormatter, log_event, request_id_ctx


def test_allowed_fields_log_successfully() -> None:
    """Allowed structured log fields must pass validation without error."""
    # Should not raise
    log_event(
        "query_processed",
        request_id="req-123",
        response_type="EXTRACTIVE",
        triage_level="SELF_CARE",
        rule_id="RULE-01",
        mode="deterministic",
        node="safety_gate",
        elapsed_ms=45,
        status_code=200,
    )


def test_disallowed_message_field_raises_error() -> None:
    """User message text is strictly prohibited from logs and must raise ValueError."""
    with pytest.raises(ValueError, match="Disallowed log fields: message"):
        log_event("user_query_received", message="I have chest pain")


def test_disallowed_arbitrary_field_raises_error() -> None:
    """Any unapproved field name must raise ValueError."""
    with pytest.raises(ValueError, match="Disallowed log fields: user_name"):
        log_event("query_event", user_name="John")


def test_json_formatter_serializes_structured_output() -> None:
    """JSONFormatter output should be valid JSON containing event fields."""
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="aira.test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test event message",
        args=(),
        exc_info=None,
    )
    record.__dict__["event_data"] = {"event_name": "test_event", "status_code": 200}

    formatted = formatter.format(record)
    parsed = json.loads(formatted)

    assert parsed["level"] == "INFO"
    assert parsed["logger"] == "aira.test"
    assert parsed["event_name"] == "test_event"
    assert parsed["status_code"] == 200
    assert "timestamp" in parsed


def test_json_formatter_includes_context_request_id() -> None:
    """JSONFormatter includes request_id from contextvar if not already present."""
    token = request_id_ctx.set("ctx-req-999")
    try:
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="aira.test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Context request test",
            args=(),
            exc_info=None,
        )
        formatted = formatter.format(record)
        parsed = json.loads(formatted)
        assert parsed["request_id"] == "ctx-req-999"
    finally:
        request_id_ctx.reset(token)
