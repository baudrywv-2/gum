"""Scoring and opportunity-report contracts (Milestone 7)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from packages.contracts.formats import SolutionFormat
from packages.contracts.opportunities import LabeledClaim


class ScoreDimension(str, Enum):
    DEMAND_EVIDENCE = "demand_evidence"
    ORGANIC_RANKING_FEASIBILITY = "organic_ranking_feasibility"
    FORMAT_FIT = "format_fit"
    BUSINESS_VIABILITY = "business_viability"
    EVIDENCE_CONFIDENCE = "evidence_confidence"
    OVERALL_PRIORITY = "overall_priority"


class ScoreExplanation(BaseModel):
    dimension: ScoreDimension
    score: float = Field(ge=0.0, le=1.0)
    weight: float = Field(ge=0.0, le=1.0, default=0.0)
    explanation: str
    claims: list[LabeledClaim] = Field(default_factory=list)
    evidence_ids: list[UUID] = Field(default_factory=list)
    inputs: dict[str, Any] = Field(default_factory=dict)
    limitations: list[str] = Field(default_factory=list)


class OpportunityScores(BaseModel):
    demand_evidence: ScoreExplanation
    organic_ranking_feasibility: ScoreExplanation
    format_fit: ScoreExplanation
    business_viability: ScoreExplanation
    evidence_confidence: ScoreExplanation
    overall_priority: ScoreExplanation


class OpportunityReport(BaseModel):
    id: UUID | None = None
    collection_id: UUID
    query: str
    title: str
    summary: str
    problem: str
    audience: str | None = None
    geography: str | None = None
    language: str | None = None
    demand_evidence: list[LabeledClaim] = Field(default_factory=list)
    search_behaviour_keywords: list[str] = Field(default_factory=list)
    discussion_evidence: list[LabeledClaim] = Field(default_factory=list)
    competitors: list[str] = Field(default_factory=list)
    competitor_weaknesses: list[LabeledClaim] = Field(default_factory=list)
    unmet_needs: list[LabeledClaim] = Field(default_factory=list)
    recommended_format: SolutionFormat | None = None
    alternative_formats: list[SolutionFormat] = Field(default_factory=list)
    scores: OpportunityScores
    complexity: str | None = None
    build_maintenance: str | None = None
    monetization_hypotheses: list[str] = Field(default_factory=list)
    risks: list[LabeledClaim] = Field(default_factory=list)
    source_urls: list[str] = Field(default_factory=list)
    timestamps: dict[str, datetime | None] = Field(default_factory=dict)
    limitations: list[str] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    missing_info: list[str] = Field(default_factory=list)
    cheapest_validation_experiment: str | None = None
    next_actions: list[str] = Field(default_factory=list)
    claims: list[LabeledClaim] = Field(default_factory=list)
    evidence_ids: list[UUID] = Field(default_factory=list)
    opportunity_ids: list[UUID] = Field(default_factory=list)
    format_recommendation_id: UUID | None = None
    gap_report_id: UUID | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None


class GenerateReportRequest(BaseModel):
    query: str = Field(min_length=1)
    geography: str | None = None
    language: str | None = None
    collection_id: UUID | None = None
    collect_if_missing: bool = True
    run_discovery: bool = True
    run_gap_analysis: bool = True
    run_format_recommendation: bool = True
    rank_by: ScoreDimension = ScoreDimension.OVERALL_PRIORITY
    min_evidence_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    min_overall_priority: float = Field(default=0.0, ge=0.0, le=1.0)
    limit: int = Field(default=20, ge=1, le=100)


class GenerateReportResult(BaseModel):
    reports: list[OpportunityReport] = Field(default_factory=list)
    collection_id: UUID
    query: str
    ranked_by: ScoreDimension
    count: int
    limitations: list[str] = Field(default_factory=list)


class RankReportsRequest(BaseModel):
    report_ids: list[UUID] = Field(default_factory=list)
    rank_by: ScoreDimension = ScoreDimension.OVERALL_PRIORITY
    min_evidence_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    min_overall_priority: float = Field(default=0.0, ge=0.0, le=1.0)
    limit: int = Field(default=50, ge=1, le=200)
