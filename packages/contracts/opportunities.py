"""Opportunity discovery contracts (Milestone 4)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from packages.contracts.claim_tags import ClaimTag
from packages.contracts.platforms import parse_platforms
from packages.contracts.providers import ProviderName


class OpportunityType(str, Enum):
    RECURRING_PROBLEM = "recurring_problem"
    EMERGING_THEME = "emerging_theme"
    UNDERSERVED_AUDIENCE = "underserved_audience"
    CROSS_SOURCE = "cross_source"


class EvidenceCluster(BaseModel):
    id: UUID | None = None
    label: str
    evidence_ids: list[UUID] = Field(default_factory=list)
    providers: list[ProviderName] = Field(default_factory=list)
    kinds: list[str] = Field(default_factory=list)
    shared_tokens: list[str] = Field(default_factory=list)
    size: int = 0
    claim_tag: ClaimTag = ClaimTag.AI_INTERPRETATION
    limitations: list[str] = Field(default_factory=list)


class EmergingTheme(BaseModel):
    theme: str
    token: str
    evidence_count: int
    provider_count: int
    providers: list[ProviderName] = Field(default_factory=list)
    evidence_ids: list[UUID] = Field(default_factory=list)
    claim_tag: ClaimTag = ClaimTag.AI_INTERPRETATION
    limitations: list[str] = Field(default_factory=list)


class UnderservedAudienceHypothesis(BaseModel):
    audience_label: str
    geography: str | None = None
    language: str | None = None
    rationale: str
    supporting_evidence_ids: list[UUID] = Field(default_factory=list)
    claim_tag: ClaimTag = ClaimTag.HYPOTHESIS
    limitations: list[str] = Field(default_factory=list)


class CrossSourceCorrelation(BaseModel):
    cluster_label: str
    providers: list[ProviderName]
    search_count: int
    discussion_count: int
    evidence_ids: list[UUID] = Field(default_factory=list)
    claim_tag: ClaimTag = ClaimTag.AI_INTERPRETATION
    limitations: list[str] = Field(default_factory=list)


class LabeledClaim(BaseModel):
    """Explicit claim with mandatory type label — never unlabeled demand."""

    text: str
    claim_tag: ClaimTag
    evidence_ids: list[UUID] = Field(default_factory=list)


class Opportunity(BaseModel):
    id: UUID | None = None
    run_id: UUID | None = None
    collection_id: UUID | None = None
    opportunity_type: OpportunityType
    title: str
    summary: str
    problem: str
    audience: str | None = None
    geography: str | None = None
    language: str | None = None
    claims: list[LabeledClaim] = Field(default_factory=list)
    evidence_ids: list[UUID] = Field(default_factory=list)
    providers: list[ProviderName] = Field(default_factory=list)
    themes: list[str] = Field(default_factory=list)
    missing_info: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    attributes: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None


class DiscoverOpportunitiesRequest(BaseModel):
    query: str = Field(min_length=1)
    geography: str | None = None
    language: str | None = None
    collection_id: UUID | None = None
    collect_if_missing: bool = True
    min_cluster_size: int = Field(default=2, ge=1, le=50)
    max_opportunities: int = Field(default=20, ge=1, le=100)
    # "all" | "youtube" | ["serp","trends","x"] — filters evidence providers.
    platforms: list[str] | str | None = None

    @field_validator("platforms")
    @classmethod
    def _validate_platforms(cls, value: list[str] | str | None) -> list[str] | str | None:
        if value is None:
            return value
        parse_platforms(value)
        return value


class DiscoverOpportunitiesResult(BaseModel):
    run_id: UUID
    collection_id: UUID
    query: str
    clusters: list[EvidenceCluster] = Field(default_factory=list)
    recurring_problems: list[Opportunity] = Field(default_factory=list)
    emerging_themes: list[EmergingTheme] = Field(default_factory=list)
    underserved_audiences: list[UnderservedAudienceHypothesis] = Field(
        default_factory=list
    )
    correlations: list[CrossSourceCorrelation] = Field(default_factory=list)
    opportunities: list[Opportunity] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    platforms_requested: list[str] = Field(default_factory=list)
    platforms_run: list[dict] = Field(default_factory=list)
