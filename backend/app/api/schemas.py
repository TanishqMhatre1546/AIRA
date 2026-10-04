"""Pydantic schemas for API request and response models."""

import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.core.graph import HelplineItem, PipelineResponse, ResponseSections
from app.core.validators import Citation

# Regex to strip ASCII control characters (0x00-0x1F, 0x7F) except \n, \r, \t
CONTROL_CHAR_REGEX = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


class IntakeAnswer(BaseModel):
    """An intake question answer containing selected option IDs."""

    question_id: str
    selected_option_ids: list[str] = Field(default_factory=list)


class IntakePayload(BaseModel):
    """Payload containing round 1 answers and optional extra text."""

    answers: list[IntakeAnswer] = Field(default_factory=list)
    extra_text: str | None = None

    @field_validator("extra_text", mode="before")
    @classmethod
    def validate_extra_text(cls, value: object) -> str | None:
        """Strip control characters and validate length up to 300 characters."""
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("Extra text must be a string")
        cleaned = CONTROL_CHAR_REGEX.sub("", value).strip()
        if len(cleaned) > 300:
            raise ValueError("Extra text must not exceed 300 characters")
        return cleaned if cleaned else None


class TriageRequest(BaseModel):
    """Request payload for symptom triage evaluation."""

    message: str
    skip_intake: bool = False
    intake: IntakePayload | None = None

    @field_validator("message", mode="before")
    @classmethod
    def validate_message(cls, value: object) -> str:
        """Strip control characters and validate message length between 2 and 500 characters."""
        if not isinstance(value, str):
            raise ValueError("Message must be a string")

        # Strip control characters
        cleaned = CONTROL_CHAR_REGEX.sub("", value).strip()

        if len(cleaned) < 2:
            raise ValueError("Message must be at least 2 characters long")
        if len(cleaned) > 500:
            raise ValueError("Message must not exceed 500 characters")

        return cleaned


class IntakeQuestionOption(BaseModel):
    """Client-facing intake option item with internal metadata stripped."""

    id: str
    label: str


class IntakeQuestion(BaseModel):
    """Client-facing intake question item."""

    id: str
    type: Literal["single_select", "multi_select"]
    text: str
    options: list[IntakeQuestionOption] = Field(default_factory=list)


class TriageResponse(BaseModel):
    """Response payload for symptom triage evaluation."""

    request_id: str
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
    disclaimer: str
    questions: list[IntakeQuestion] = Field(default_factory=list)
    allow_text: bool = False
    text_max: int = 300
    skip_allowed: bool = False
    answers_summary: list[str] = Field(default_factory=list)

    @classmethod
    def from_pipeline_response(cls, resp: PipelineResponse, request_id: str) -> "TriageResponse":
        """Construct a TriageResponse from a PipelineResponse and request identifier."""
        return cls(
            request_id=request_id,
            response_type=resp.response_type,
            triage_level=resp.triage_level,
            headline=resp.headline,
            message=resp.message,
            helplines=resp.helplines,
            sections=resp.sections,
            citations=resp.citations,
            mode=resp.mode,
            disclaimer=resp.disclaimer,
            questions=[
                IntakeQuestion.model_validate(q) if isinstance(q, dict) else q
                for q in resp.questions
            ],
            allow_text=resp.allow_text,
            text_max=resp.text_max,
            skip_allowed=resp.skip_allowed,
            answers_summary=resp.answers_summary,
        )


class HealthResponse(BaseModel):
    """Liveness health check response."""

    status: str = "ok"


class ReadyResponse(BaseModel):
    """Readiness probe success response."""

    status: str = "ready"


class NotReadyResponse(BaseModel):
    """Readiness probe unavailable response."""

    status: str = "not_ready"
    reason: str


class ClinicalReviewStatus(BaseModel):
    """Clinical review validation status."""

    reviewed: bool
    reviewer: str | None = None
    date: str | None = None


class CountsMeta(BaseModel):
    """Entity counts for metadata endpoint."""

    conditions: int
    chunks: int
    rules: int


class MetaResponse(BaseModel):
    """Corpus, rule, and system metadata response."""

    version: str
    corpus_hash: str
    rule_table_version: str
    counts: CountsMeta
    supported_conditions: list[str]
    clinical_review_status: ClinicalReviewStatus
    disclaimer: str
    content_verification: Literal["verified", "unverified"] = "verified"


class SourceItem(BaseModel):
    """Information for an authoritative clinical guideline source."""

    title: str
    publisher: str
    edition_year: str | int | None = None
    url: str | None = None
    conditions: list[str] = Field(default_factory=list)


class SourcesResponse(BaseModel):
    """Listing of all authoritative sources backing AIRA."""

    sources: list[SourceItem]


class ErrorResponse(BaseModel):
    """Generic error response with emergency helplines."""

    detail: str
    request_id: str
    helplines: list[HelplineItem] = Field(default_factory=list)
