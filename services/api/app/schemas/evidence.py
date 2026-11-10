"""API schemas for evidence collection endpoints."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field

from packages.contracts.evidence import (
    CollectEvidenceRequest,
    CollectEvidenceResult,
    EvidenceKind,
    EvidenceRecord,
    PainPoint,
)


class CollectEvidenceBody(CollectEvidenceRequest):
    """POST /evidence/collect body."""


class CollectEvidenceResponse(CollectEvidenceResult):
    pass


class EvidenceListResponse(BaseModel):
    evidence: list[EvidenceRecord]
    count: int


class PainPointListResponse(BaseModel):
    pain_points: list[PainPoint]
    count: int


class EvidenceCollectionSummary(BaseModel):
    collection_id: UUID
    query: str
    geography: str | None = None
    language: str | None = None
    status: str
    evidence_count: int = 0
    pain_point_count: int = 0


class EvidenceQueryParams(BaseModel):
    collection_id: UUID | None = None
    kind: EvidenceKind | None = None
    limit: int = Field(default=100, ge=1, le=500)
