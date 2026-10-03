"""Unit tests for configuration validation and production invariants."""

import pytest
from pydantic import ValidationError

from app.config import Settings


def test_production_fails_without_api_key_when_llm_enabled() -> None:
    """Production mode must reject startup if LLM is enabled but no API key is provided."""
    with pytest.raises(ValidationError, match="gemini_api_key is required in production"):
        Settings(
            environment="production",
            llm_enabled=True,
            gemini_api_key=None,
            allow_unverified_content=False,
        )


def test_production_fails_with_unverified_content() -> None:
    """Production mode must reject startup if allow_unverified_content is True."""
    with pytest.raises(
        ValidationError, match="allow_unverified_content must be False in production"
    ):
        Settings(
            environment="production",
            llm_enabled=False,
            allow_unverified_content=True,
        )


def test_production_succeeds_with_valid_settings() -> None:
    """Production mode initializes properly when invariants are satisfied."""
    cfg = Settings(
        environment="production",
        llm_enabled=True,
        gemini_api_key="valid_test_key",  # type: ignore[arg-type]
        allow_unverified_content=False,
    )
    assert cfg.environment == "production"
    assert cfg.gemini_api_key is not None
    assert cfg.gemini_api_key.get_secret_value() == "valid_test_key"


def test_development_allows_missing_key() -> None:
    """Development mode allows starting without an API key."""
    cfg = Settings(
        environment="development",
        llm_enabled=True,
        gemini_api_key=None,
        allow_unverified_content=True,
    )
    assert cfg.environment == "development"
