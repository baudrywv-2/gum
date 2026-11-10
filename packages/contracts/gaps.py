"""Competitor and gap-analysis contracts (Milestone 5)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from packages.contracts.claim_tags import ClaimTag
from packages.contracts.opportunities import LabeledClaim
from packages.contracts.providers import ProviderName


class CompetitorStatus(str, Enum):
    """Never mark weak without supporting evidence."""

    OBSERVED_IN_SEARCH = "observed_in_search"
    MENTIONED_IN_FEEDBACK = "mentioned_in_feedback"
    WEAKNESS_EVIDENCED = "weakness_evidenced"
    NO_WEAKNESS_EVIDENCE = "no_weakness_evidence"


class GapKind(str, Enum):
    MISSING_FEATURE = "missing_feature"
    MISSING_CONTENT = "missing_content"
    SEARCH_FEEDBACK_MISMATCH = "search_feedback_mismatch"
    COMPETITOR_WEAKNESS = "competitor_weakness"


class CompetitorProfile(BaseModel):
    id: UUID | None = None
    name: str
    url: str | None = None
    source_providers: list[ProviderName] = Field(default_factory=list)
    search_evidence_ids: list[UUID] = Field(default_factory=list)
    feedback_evidence_ids: list[UUID] = Field(default_factory=list)
    status: CompetitorStatus = CompetitorStatus.OBSERVED_IN_SEARCH
    claims: list[LabeledClaim] = Field(default_factory=list)
    weaknesses: list[LabeledClaim] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    attributes: dict[str, Any] = Field(default_factory=dict)


class GapFinding(BaseModel):
    id: UUID | None = None
    kind: GapKind
    title: str
    summary: str
    claims: list[LabeledClaim] = Field(default_factory=list)
    evidence_ids: list[UUID] = Field(default_factory=list)
    competitor_name: str | None = None
    missing_info: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    attributes: dict[str, Any] = Field(default_factory=dict)


class GapReport(BaseModel):
    id: UUID | None = None
    collection_id: UUID
    query: str
    geography: str | None = None
    language: str | None = None
    competitors: list[CompetitorProfile] = Field(default_factory=list)
    findings: list[GapFinding] = Field(default_factory=list)
    search_vs_feedback: str
    claims: list[LabeledClaim] = Field(default_factory=list)
    missing_info: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    created_at: datetime | None = None


class AnalyzeGapsRequest(BaseModel):
    query: str = Field(min_length=1)
    geography: str | None = None
    language: str | None = None
    collection_id: UUID | None = None
    collect_if_missing: bool = True
    max_competitors: int = Field(default=20, ge=1, le=100)
    max_findings: int = Field(default=50, ge=1, le=200)


class AnalyzeGapsResult(BaseModel):
    report_id: UUID
    collection_id: UUID
    query: str
    report: GapReport
    limitations: list[str] = Field(default_factory=list)
