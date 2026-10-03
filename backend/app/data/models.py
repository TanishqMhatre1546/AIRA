"""Domain models and Pydantic schemas for curated guidelines and urgency rules."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ConditionSource(BaseModel):
    """Source reference information for a clinical guideline document."""

    model_config = ConfigDict(extra="allow")

    title: str
    publisher: str
    edition_year: str
    url: str
    retrieved: str | None = None
    source_pages: str | None = None
    restricted_content_excluded: list[str] = Field(default_factory=list)


class ConditionSection(BaseModel):
    """Individual section containing a list of clinical guidance items."""

    model_config = ConfigDict(extra="allow")

    type: Literal["danger_signs", "self_care", "see_doctor", "refer_urgently"] | str
    label: str
    page: int | None = None
    items: list[str] = Field(default_factory=list)


class ConditionDocument(BaseModel):
    """Curated clinical guideline document for a specific health condition."""

    model_config = ConfigDict(extra="allow")

    id: str
    condition: str
    icd_code: str
    source: ConditionSource
    sections: list[ConditionSection] = Field(default_factory=list)
    condition_description: str | dict[str, str] | None = None
    types_covered: list[str] | dict[str, Any] | None = None
    critical_note: str | dict[str, Any] | None = None
    scope_note: str | None = None
    screening_note: str | dict[str, Any] | None = None
    dehydration_assessment: dict[str, Any] | str | None = None
    high_risk_groups: list[str] | dict[str, Any] | None = None
    prevention_note: str | dict[str, Any] | None = None
    review: dict[str, Any] | None = None


class RuleMatch(BaseModel):
    """Trigger phrases and conjunction requirements for rule activation."""

    model_config = ConfigDict(extra="allow")

    phrases: list[str] = Field(default_factory=list)
    requires_all: list[list[str]] = Field(default_factory=list)


class UrgencyRule(BaseModel):
    """Deterministic triage mapping rule (Schema v2)."""

    model_config = ConfigDict(extra="allow")

    id: str
    kind: Literal["emergency", "crisis", "refusal", "scope", "see_doctor", "self_care"] | str = (
        "emergency"
    )
    condition: str
    source_id: str | None = None
    source_page: int | None = None
    match: RuleMatch = Field(default_factory=RuleMatch)
    negatable: bool = True
    response: str | None = None
    review_status: str | None = None

    # Backwards compatibility helpers
    trigger_keywords: list[str] | None = None
    triage_level: str | None = None


class UrgencyRulesFile(BaseModel):
    """Complete structure of urgency_rules.json (Schema v2 with v1 backward compatibility)."""

    model_config = ConfigDict(extra="allow")

    meta: dict[str, Any] = Field(default_factory=dict)
    rules: list[UrgencyRule] = Field(default_factory=list)
    emergency_rules: list[UrgencyRule] = Field(default_factory=list)
    see_doctor_rules: list[UrgencyRule] = Field(default_factory=list)
    self_care_rules: list[UrgencyRule] = Field(default_factory=list)


class GuidelineChunk(BaseModel):
    """Extracted text chunk from clinical guidelines with provenance metadata."""

    model_config = ConfigDict(extra="allow")

    chunk_id: str
    condition_id: str
    condition: str
    section_type: str
    label: str
    text: str
    item_ids: list[str] = Field(default_factory=list)
    source_title: str
    source_publisher: str
    source_year: str
    source_url: str
    page: int | None = None


class ProvenanceRecord(BaseModel):
    """Provenance review entry for a single extracted clinical item."""

    model_config = ConfigDict(extra="allow")

    item_id: str
    condition_id: str
    section_type: str
    page: int | None = None
    text: str
    status: Literal["unverified", "verified", "unsupported"] = "unverified"
    reviewer: str | None = None
    reviewed_on: str | None = None
    note: str | None = None
