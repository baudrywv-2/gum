"""API schemas for format recommendation."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel

from packages.contracts.formats import (
    FormatRecommendation,
    RecommendFormatsRequest,
    RecommendFormatsResult,
)


class RecommendFormatsBody(RecommendFormatsRequest):
    pass


class RecommendFormatsResponse(RecommendFormatsResult):
    pass


class FormatRecommendationListResponse(BaseModel):
    recommendations: list[FormatRecommendation]
    count: int


class FormatRecommendationSummary(BaseModel):
    recommendation_id: UUID
    collection_id: UUID
    query: str
    primary_format: str
    alternative_count: int
    rejected_count: int
