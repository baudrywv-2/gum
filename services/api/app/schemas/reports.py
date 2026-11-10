"""API schemas for scoring and reports."""

from __future__ import annotations

from pydantic import BaseModel

from packages.contracts.scoring import (
    GenerateReportRequest,
    GenerateReportResult,
    OpportunityReport,
    RankReportsRequest,
)


class GenerateReportBody(GenerateReportRequest):
    pass


class GenerateReportResponse(GenerateReportResult):
    pass


class RankReportsBody(RankReportsRequest):
    pass


class ReportListResponse(BaseModel):
    reports: list[OpportunityReport]
    count: int
