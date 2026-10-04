"""Structured JSON logging configuration for AIRA."""

import json
import logging
import sys
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

# ContextVar holding the current request identifier
request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)

# Whitelisted field names allowed in structured log events
ALLOWED_LOG_FIELDS: frozenset[str] = frozenset(
    {
        "request_id",
        "response_type",
        "triage_level",
        "rule_id",
        "mode",
        "node",
        "elapsed_ms",
        "status_code",
        "intake_shown",
        "intake_skipped",
        "intake_questions_count",
    }
)


class JSONFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include structured event attributes if present
        if hasattr(record, "event_data") and isinstance(record.event_data, dict):
            payload.update(record.event_data)

        req_id = request_id_ctx.get()
        if req_id and "request_id" not in payload:
            payload["request_id"] = req_id

        return json.dumps(payload)


def setup_logging(log_level: str = "INFO") -> None:
    """Configure the root logger with JSON stdout output."""
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level.upper())

    # Clear existing handlers
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    root_logger.addHandler(handler)


def log_event(name: str, **fields: Any) -> None:
    """Log a structured event with strict field validation.

    Only approved metadata fields are permitted. User message text is strictly rejected.
    """
    disallowed_fields = set(fields.keys()) - ALLOWED_LOG_FIELDS
    if disallowed_fields:
        sorted_fields = ", ".join(sorted(disallowed_fields))
        raise ValueError(f"Disallowed log fields: {sorted_fields}")

    logger = logging.getLogger("aira.events")
    # Attach permitted fields in extra
    record_data = {"event_name": name, **fields}
    logger.info(name, extra={"event_data": record_data})
