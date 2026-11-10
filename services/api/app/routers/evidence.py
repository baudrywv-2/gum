"""Evidence collection API (Milestone 3)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.evidence import (
    CollectEvidenceBody,
    CollectEvidenceResponse,
    EvidenceCollectionSummary,
    EvidenceListResponse,
    PainPointListResponse,
)
from database.models import EvidenceCollection, EvidenceRecordRow, PainPointRow
from evidence.collector import EvidenceCollector
from evidence.store import EvidenceStore
from packages.contracts.evidence import EvidenceKind

router = APIRouter(prefix="/evidence", tags=["evidence"])


@router.post("/collect", response_model=CollectEvidenceResponse)
def collect_evidence(
    body: CollectEvidenceBody, db: Session = Depends(get_db)
) -> CollectEvidenceResponse:
    collector = EvidenceCollector(db)
    result = collector.collect(body)
    return CollectEvidenceResponse.model_validate(result.model_dump())


@router.get("", response_model=EvidenceListResponse)
def list_evidence(
    collection_id: UUID | None = None,
    kind: EvidenceKind | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> EvidenceListResponse:
    store = EvidenceStore(db)
    rows = store.list_evidence(collection_id=collection_id, kind=kind, limit=limit)
    return EvidenceListResponse(evidence=rows, count=len(rows))


@router.get("/pain-points", response_model=PainPointListResponse)
def list_pain_points(
    collection_id: UUID | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> PainPointListResponse:
    store = EvidenceStore(db)
    rows = store.list_pain_points(collection_id=collection_id, limit=limit)
    return PainPointListResponse(pain_points=rows, count=len(rows))


@router.get("/collections/{collection_id}", response_model=EvidenceCollectionSummary)
def get_collection(
    collection_id: UUID, db: Session = Depends(get_db)
) -> EvidenceCollectionSummary:
    collection = db.get(EvidenceCollection, collection_id)
    if collection is None:
        raise HTTPException(status_code=404, detail="Collection not found")
    evidence_count = db.scalar(
        select(func.count())
        .select_from(EvidenceRecordRow)
        .where(EvidenceRecordRow.collection_id == collection_id)
    )
    pain_count = db.scalar(
        select(func.count())
        .select_from(PainPointRow)
        .where(PainPointRow.collection_id == collection_id)
    )
    return EvidenceCollectionSummary(
        collection_id=collection.id,
        query=collection.query,
        geography=collection.geography,
        language=collection.language,
        status=collection.status,
        evidence_count=int(evidence_count or 0),
        pain_point_count=int(pain_count or 0),
    )
