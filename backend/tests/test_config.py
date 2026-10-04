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


def test_staging_allows_unverified_content() -> None:
    """Staging mode allows unverified content for demos."""
    cfg = Settings(
        environment="staging",
        llm_enabled=False,
        allow_unverified_content=True,
    )
    assert cfg.environment == "staging"
    assert cfg.allow_unverified_content is True


def test_test_environment_allows_unverified_content() -> None:
    """Test environment allows unverified content."""
    cfg = Settings(
        environment="test",
        llm_enabled=False,
        allow_unverified_content=True,
    )
    assert cfg.environment == "test"
    assert cfg.allow_unverified_content is True


def test_invalid_environment_raises_validation_error() -> None:
    """Settings rejects unrecognized environment names."""
    with pytest.raises(ValidationError):
        Settings(
            environment="sandbox",  # type: ignore[arg-type]
        )


def test_retriever_refuses_unverified_index_in_production(tmp_path: pytest.TempPathFactory) -> None:
    """Retriever.from_disk must refuse an index with include_unverified=True in production."""
    from app.core.retriever import Retriever

    prod_settings = Settings(
        environment="production",
        llm_enabled=False,
        allow_unverified_content=False,
    )

    with pytest.raises(
        ValueError,
        match="Production environment cannot start with an index built",
    ):
        Retriever.from_disk(settings=prod_settings)


def test_retriever_allows_unverified_index_in_staging() -> None:
    """Retriever.from_disk allows an index with include_unverified=True in staging."""
    from app.core.retriever import Retriever

    staging_settings = Settings(
        environment="staging",
        llm_enabled=False,
        allow_unverified_content=True,
    )

    retriever = Retriever.from_disk(settings=staging_settings)
    assert retriever is not None
    assert len(retriever.chunks) > 0
