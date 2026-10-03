"""Configuration settings for the AIRA backend application."""

import json
from pathlib import Path
from typing import Literal

from pydantic import SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: Literal["development", "production", "test"] = "development"
    log_level: str = "INFO"
    cors_origins: str | list[str] = ["http://localhost:5173", "http://localhost:3000"]

    @field_validator("cors_origins", mode="after")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Parse CORS origins from JSON list, comma-separated string, or list."""
        if isinstance(v, str):
            v_trimmed = v.strip()
            if v_trimmed.startswith("[") and v_trimmed.endswith("]"):
                try:
                    parsed = json.loads(v_trimmed)
                    if isinstance(parsed, list):
                        return [str(item).strip() for item in parsed if item]
                except Exception:
                    pass
            return [origin.strip() for origin in v_trimmed.split(",") if origin.strip()]
        return v
    gemini_api_key: SecretStr | None = None
    chat_model: str = "gemini-2.5-flash"
    embedding_model: str = "gemini-embedding-001"
    llm_enabled: bool = True
    max_input_chars: int = 500
    top_k: int = 5
    retrieval_min_cosine: float = 0.65
    retrieval_min_bm25: float = 2.0
    retrieval_timeout_seconds: float = 5.0
    rate_limit_per_minute: int = 20
    daily_model_call_budget: int = 1000
    max_request_body_bytes: int = 4096
    llm_timeout_seconds: int = 12
    groundedness_threshold: float = 0.4
    data_dir: Path = Path("./data")
    allow_unverified_content: bool = False
    clinical_review_done: bool = False
    clinical_review_by: str | None = None
    clinical_review_date: str | None = None

    @model_validator(mode="after")
    def validate_production_invariants(self) -> "Settings":
        """Validate safety constraints when running in production."""
        if self.environment == "production":
            if self.allow_unverified_content:
                raise ValueError("allow_unverified_content must be False in production")
            if self.llm_enabled and (
                self.gemini_api_key is None or not self.gemini_api_key.get_secret_value().strip()
            ):
                raise ValueError(
                    "gemini_api_key is required in production when llm_enabled is True"
                )
        return self


settings = Settings()
