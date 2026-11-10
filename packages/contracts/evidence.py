"""Evidence collection contracts (Milestone 3)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from packages.contracts.claim_tags import ClaimTag
from packages.contracts.providers import ProviderMode, ProviderName


class EvidenceKind(str, Enum):
    SEARCH = "search"
    DISCUSSION = "discussion"
    PAIN_POINT = "pain_point"


class ReliabilityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNKNOWN = "unknown"


class Provenance(BaseModel):
    """Traceability metadata required for every evidence record."""

    provider: ProviderName
    provider_mode: ProviderMode
    source_url: str | None = None
    query: str | None = None
    geography: str | None = None
    language: str | None = None
    collected_at: datetime
    claim_tag: ClaimTag = ClaimTag.UNVERIFIED_CLAIM
    reliability: ReliabilityLevel = ReliabilityLevel.LOW
    limitations: list[str] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)


class EvidenceRecord(BaseModel):
    id: UUID | None = None
    collection_id: UUID | None = None
    kind: EvidenceKind
    title: str
    summary: str
    fingerprint: str
    provenance: Provenance
    attributes: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    is_duplicate: bool = False


class PainPoint(BaseModel):
    id: UUID | None = None
    collection_id: UUID | None = None
    text: str
    normalized_text: str
    frequency: int = 1
    claim_tag: ClaimTag = ClaimTag.AI_INTERPRETATION
    evidence_ids: list[UUID] = Field(default_factory=list)
    source_providers: list[ProviderName] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    created_at: datetime | None = None


class CollectEvidenceRequest(BaseModel):
    query: str = Field(min_length=1)
    geography: str | None = None
    language: str | None = None
    include_search: bool = True
    include_discussions: bool = True
    extract_pain_points: bool = True
    providers_search: list[ProviderName] = Field(
        default_factory=lambda: [
            ProviderName.GOOGLE_TRENDS,
            ProviderName.SERP,
            ProviderName.YOUTUBE,
        ]
    )
    providers_discussion: list[ProviderName] = Field(
        # X only by default — do not inject MOCK discussion when X is down.
        default_factory=lambda: [ProviderName.X_API]
    )
    limit_per_provider: int = Field(default=5, ge=1, le=50)


class CollectEvidenceResult(BaseModel):
    collection_id: UUID
    query: str
    evidence_created: int
    evidence_deduplicated: int
    pain_points_created: int
    pain_points_updated: int
    evidence: list[EvidenceRecord] = Field(default_factory=list)
    pain_points: list[PainPoint] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
