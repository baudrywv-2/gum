"""API schemas for opportunity discovery."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field

from packages.contracts.opportunities import (
    DiscoverOpportunitiesRequest,
    DiscoverOpportunitiesResult,
    Opportunity,
)


class DiscoverBody(DiscoverOpportunitiesRequest):
    pass


class DiscoverResponse(DiscoverOpportunitiesResult):
    pass


class OpportunityListResponse(BaseModel):
    opportunities: list[Opportunity]
    count: int


class OpportunityRunSummary(BaseModel):
    run_id: UUID
    collection_id: UUID
    query: str
    geography: str | None = None
    language: str | None = None
    status: str
    opportunity_count: int = 0
