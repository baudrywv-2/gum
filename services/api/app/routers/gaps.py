"""Competitor and gap analysis API (Milestone 5)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.gaps import (
    AnalyzeGapsBody,
    AnalyzeGapsResponse,
    GapReportListResponse,
    GapReportSummary,
)
from gap_engine.analyze import GapAnalysisEngine
from gap_engine.store import GapStore
from packages.contracts.gaps import GapReport

router = APIRouter(prefix="/gaps", tags=["gaps"])


@router.post("/analyze", response_model=AnalyzeGapsResponse)
def analyze_gaps(
    body: AnalyzeGapsBody, db: Session = Depends(get_db)
) -> AnalyzeGapsResponse:
    engine = GapAnalysisEngine(db)
    try:
        result = engine.analyze(body)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return AnalyzeGapsResponse.model_validate(result.model_dump())


@router.get("", response_model=GapReportListResponse)
def list_gap_reports(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> GapReportListResponse:
    store = GapStore(db)
    reports = [r for r in store.list_reports(limit=limit) if r is not None]
    return GapReportListResponse(reports=reports, count=len(reports))


@router.get("/{report_id}", response_model=GapReport)
def get_gap_report(report_id: UUID, db: Session = Depends(get_db)) -> GapReport:
    store = GapStore(db)
    report = store.get_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Gap report not found")
    return report


@router.get("/{report_id}/summary", response_model=GapReportSummary)
def get_gap_report_summary(
    report_id: UUID, db: Session = Depends(get_db)
) -> GapReportSummary:
    store = GapStore(db)
    report = store.get_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Gap report not found")
    return GapReportSummary(
        report_id=report.id,
        collection_id=report.collection_id,
        query=report.query,
        competitor_count=len(report.competitors),
        finding_count=len(report.findings),
    )
