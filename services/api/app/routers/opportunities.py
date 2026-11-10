"""Opportunity discovery API (Milestone 4)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.opportunities import (
    DiscoverBody,
    DiscoverResponse,
    OpportunityListResponse,
    OpportunityRunSummary,
)
from database.models import OpportunityRow, OpportunityRun
from opportunity_engine.discover import OpportunityDiscoveryEngine
from opportunity_engine.store import OpportunityStore

router = APIRouter(prefix="/opportunities", tags=["opportunities"])


@router.post("/discover", response_model=DiscoverResponse)
def discover_opportunities(
    body: DiscoverBody, db: Session = Depends(get_db)
) -> DiscoverResponse:
    engine = OpportunityDiscoveryEngine(db)
    try:
        result = engine.discover(body)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return DiscoverResponse.model_validate(result.model_dump())


@router.get("", response_model=OpportunityListResponse)
def list_opportunities(
    run_id: UUID | None = None,
    collection_id: UUID | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> OpportunityListResponse:
    store = OpportunityStore(db)
    rows = store.list_opportunities(
        run_id=run_id, collection_id=collection_id, limit=limit
    )
    return OpportunityListResponse(opportunities=rows, count=len(rows))


@router.get("/runs/{run_id}", response_model=OpportunityRunSummary)
def get_run(run_id: UUID, db: Session = Depends(get_db)) -> OpportunityRunSummary:
    run = db.get(OpportunityRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Discovery run not found")
    count = db.scalar(
        select(func.count())
        .select_from(OpportunityRow)
        .where(OpportunityRow.run_id == run_id)
    )
    return OpportunityRunSummary(
        run_id=run.id,
        collection_id=run.collection_id,
        query=run.query,
        geography=run.geography,
        language=run.language,
        status=run.status,
        opportunity_count=int(count or 0),
    )
