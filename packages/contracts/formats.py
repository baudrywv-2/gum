"""Format recommendation contracts (Milestone 6)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from packages.contracts.claim_tags import ClaimTag
from packages.contracts.opportunities import LabeledClaim


class SolutionFormat(str, Enum):
    SEO_WEBSITE_BLOG = "seo_website_blog"
    ANDROID_APP = "android_app"
    IOS_APP = "ios_app"
    WEB_APP = "web_app"
    YOUTUBE = "youtube"
    CALCULATOR_TOOL = "calculator_tool"
    DIRECTORY = "directory"
    MARKETPLACE = "marketplace"
    NEWSLETTER_ALERTS = "newsletter_alerts"
    SAAS = "saas"
    API_DATA_SERVICE = "api_data_service"
    AI_AGENT = "ai_agent"
    DIGITAL_PRODUCT = "digital_product"
    PROFESSIONAL_SERVICES = "professional_services"


class ComplexityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class FormatDecision(str, Enum):
    PRIMARY = "primary"
    ALTERNATIVE = "alternative"
    COMPLEMENTARY = "complementary"
    REJECTED = "rejected"


class FormatProfile(BaseModel):
    format: SolutionFormat
    label: str
    complexity: ComplexityLevel
    maintenance: ComplexityLevel
    monetization_hypotheses: list[str] = Field(default_factory=list)
    cheapest_validation: str
    default_preference_rank: int = Field(
        description="Lower means simpler / preferred when evidence is equal"
    )


class FormatEvaluation(BaseModel):
    format: SolutionFormat
    decision: FormatDecision
    fit_score: float = Field(ge=0.0, le=1.0)
    complexity: ComplexityLevel
    maintenance: ComplexityLevel
    monetization_hypotheses: list[str] = Field(default_factory=list)
    cheapest_validation: str
    reasons_selected: list[LabeledClaim] = Field(default_factory=list)
    reasons_rejected: list[LabeledClaim] = Field(default_factory=list)
    evidence_ids: list[UUID] = Field(default_factory=list)
    missing_info: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    attributes: dict[str, Any] = Field(default_factory=dict)


class FormatRecommendation(BaseModel):
    id: UUID | None = None
    collection_id: UUID
    query: str
    geography: str | None = None
    language: str | None = None
    primary_format: SolutionFormat
    alternatives: list[SolutionFormat] = Field(default_factory=list)
    complementary: list[SolutionFormat] = Field(default_factory=list)
    rejected: list[SolutionFormat] = Field(default_factory=list)
    evaluations: list[FormatEvaluation] = Field(default_factory=list)
    summary: str
    claims: list[LabeledClaim] = Field(default_factory=list)
    missing_info: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    created_at: datetime | None = None


class RecommendFormatsRequest(BaseModel):
    query: str = Field(min_length=1)
    geography: str | None = None
    language: str | None = None
    collection_id: UUID | None = None
    collect_if_missing: bool = True
    run_gap_analysis: bool = True
    max_alternatives: int = Field(default=3, ge=0, le=10)
    max_complementary: int = Field(default=3, ge=0, le=10)


class RecommendFormatsResult(BaseModel):
    recommendation_id: UUID
    collection_id: UUID
    query: str
    recommendation: FormatRecommendation
    limitations: list[str] = Field(default_factory=list)
