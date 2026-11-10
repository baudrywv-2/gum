"""Provider contracts shared across API and provider adapters (Milestone 2)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from packages.contracts.claim_tags import ClaimTag


class ProviderName(str, Enum):
    MOCK = "mock"
    GOOGLE_ADS = "google_ads"
    GOOGLE_TRENDS = "google_trends"
    SERP = "serp"
    X_API = "x_api"
    YOUTUBE = "youtube"
    REDDIT = "reddit"


class ProviderMode(str, Enum):
    """How an adapter is currently operating."""

    MOCK = "mock"
    LIVE = "live"
    UNAVAILABLE = "unavailable"


class ProviderCapability(str, Enum):
    KEYWORD_IDEAS = "keyword_ideas"
    TREND_INTEREST = "trend_interest"
    SERP_SNAPSHOT = "serp_snapshot"
    SOCIAL_SEARCH = "social_search"
    VIDEO_SEARCH = "video_search"
    GENERIC_SEARCH = "generic_search"


class ProviderRequest(BaseModel):
    query: str = Field(min_length=1)
    geography: str | None = None
    language: str | None = None
    limit: int = Field(default=10, ge=1, le=100)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProviderResultItem(BaseModel):
    title: str
    snippet: str | None = None
    url: str | None = None
    score: float | None = None
    claim_tag: ClaimTag = ClaimTag.UNVERIFIED_CLAIM
    attributes: dict[str, Any] = Field(default_factory=dict)


class ProviderResponse(BaseModel):
    provider: ProviderName
    mode: ProviderMode
    query: str
    summary: str
    claim_tag: ClaimTag = ClaimTag.UNVERIFIED_CLAIM
    fetched_at: datetime
    cached: bool = False
    items: list[ProviderResultItem] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)


class ProviderStatus(BaseModel):
    name: ProviderName
    mode: ProviderMode
    configured: bool
    capabilities: list[ProviderCapability]
    notes: str


class ProviderUsageRecord(BaseModel):
    provider: ProviderName
    operation: str
    mode: ProviderMode
    units: int = 1
    estimated_cost_usd: float = 0.0
    success: bool = True
    cached: bool = False
    query: str | None = None
    recorded_at: datetime
    details: dict[str, Any] = Field(default_factory=dict)


# Backward-compatible alias used by Milestone 1 tests/docs.
class MockProviderResult(ProviderResponse):
    """Deprecated alias — prefer ProviderResponse."""

    provider: ProviderName = ProviderName.MOCK
