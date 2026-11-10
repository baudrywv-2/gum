"""API schemas for competitor/gap analysis."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel

from packages.contracts.gaps import AnalyzeGapsRequest, AnalyzeGapsResult, GapReport


class AnalyzeGapsBody(AnalyzeGapsRequest):
    pass


class AnalyzeGapsResponse(AnalyzeGapsResult):
    pass


class GapReportListResponse(BaseModel):
    reports: list[GapReport]
    count: int


class GapReportSummary(BaseModel):
    report_id: UUID
    collection_id: UUID
    query: str
    competitor_count: int
    finding_count: int
