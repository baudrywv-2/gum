"""Format recommendation API (Milestone 6)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.formats import (
    FormatRecommendationListResponse,
    FormatRecommendationSummary,
    RecommendFormatsBody,
    RecommendFormatsResponse,
)
from format_engine.recommend import FormatRecommender
from format_engine.store import FormatStore
from packages.contracts.formats import FormatRecommendation

router = APIRouter(prefix="/formats", tags=["formats"])


@router.post("/recommend", response_model=RecommendFormatsResponse)
def recommend_formats(
    body: RecommendFormatsBody, db: Session = Depends(get_db)
) -> RecommendFormatsResponse:
    engine = FormatRecommender(db)
    try:
        result = engine.recommend(body)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return RecommendFormatsResponse.model_validate(result.model_dump())


@router.get("", response_model=FormatRecommendationListResponse)
def list_format_recommendations(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> FormatRecommendationListResponse:
    store = FormatStore(db)
    rows = store.list_recommendations(limit=limit)
    return FormatRecommendationListResponse(recommendations=rows, count=len(rows))


@router.get("/{recommendation_id}", response_model=FormatRecommendation)
def get_format_recommendation(
    recommendation_id: UUID, db: Session = Depends(get_db)
) -> FormatRecommendation:
    store = FormatStore(db)
    row = store.get_recommendation(recommendation_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Format recommendation not found")
    return row


@router.get("/{recommendation_id}/summary", response_model=FormatRecommendationSummary)
def get_format_recommendation_summary(
    recommendation_id: UUID, db: Session = Depends(get_db)
) -> FormatRecommendationSummary:
    store = FormatStore(db)
    row = store.get_recommendation(recommendation_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Format recommendation not found")
    return FormatRecommendationSummary(
        recommendation_id=row.id,
        collection_id=row.collection_id,
        query=row.query,
        primary_format=row.primary_format.value,
        alternative_count=len(row.alternatives),
        rejected_count=len(row.rejected),
    )
