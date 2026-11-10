"""Provider stub contracts — mock only in Milestone 1."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from packages.contracts.claim_tags import ClaimTag


class ProviderName(str, Enum):
    MOCK = "mock"
    GOOGLE_ADS = "google_ads"
    GOOGLE_TRENDS = "google_trends"
    SERP = "serp"
    X_API = "x_api"
    REDDIT = "reddit"


class MockProviderResult(BaseModel):
    """Placeholder result from a mock data provider."""

    provider: ProviderName = ProviderName.MOCK
    query: str
    summary: str
    claim_tag: ClaimTag = ClaimTag.UNVERIFIED_CLAIM
    fetched_at: datetime
    raw: dict = Field(default_factory=dict)
