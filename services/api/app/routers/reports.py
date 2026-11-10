"""Scoring and opportunity report API (Milestone 7)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.reports import (
    GenerateReportBody,
    GenerateReportResponse,
    RankReportsBody,
    ReportListResponse,
)
from packages.contracts.scoring import OpportunityReport, ScoreDimension
from scoring_engine.report import ReportEngine
from scoring_engine.store import ScoringStore

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/generate", response_model=GenerateReportResponse)
def generate_reports(
    body: GenerateReportBody, db: Session = Depends(get_db)
) -> GenerateReportResponse:
    engine = ReportEngine(db)
    try:
        result = engine.generate(body)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return GenerateReportResponse.model_validate(result.model_dump())


@router.post("/rank", response_model=ReportListResponse)
def rank_reports(
    body: RankReportsBody, db: Session = Depends(get_db)
) -> ReportListResponse:
    engine = ReportEngine(db)
    rows = engine.rank_existing(body)
    return ReportListResponse(reports=rows, count=len(rows))


@router.get("", response_model=ReportListResponse)
def list_reports(
    limit: int = Query(default=50, ge=1, le=200),
    rank_by: ScoreDimension = Query(default=ScoreDimension.OVERALL_PRIORITY),
    min_evidence_confidence: float = Query(default=0.0, ge=0.0, le=1.0),
    min_overall_priority: float = Query(default=0.0, ge=0.0, le=1.0),
    db: Session = Depends(get_db),
) -> ReportListResponse:
    engine = ReportEngine(db)
    rows = engine.rank_existing(
        RankReportsBody(
            report_ids=[],
            rank_by=rank_by,
            min_evidence_confidence=min_evidence_confidence,
            min_overall_priority=min_overall_priority,
            limit=limit,
        )
    )
    return ReportListResponse(reports=rows, count=len(rows))


@router.get("/{report_id}", response_model=OpportunityReport)
def get_report(report_id: UUID, db: Session = Depends(get_db)) -> OpportunityReport:
    store = ScoringStore(db)
    row = store.get_report(report_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Opportunity report not found")
    return row
