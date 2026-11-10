"""API schemas for provider endpoints."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from packages.contracts.providers import (
    ProviderRequest,
    ProviderResponse,
    ProviderStatus,
)


class ProviderListResponse(BaseModel):
    providers: list[ProviderStatus]
    force_mock: bool
    cache: dict[str, Any]


class ProviderSearchBody(BaseModel):
    query: str = Field(min_length=1)
    geography: str | None = None
    language: str | None = None
    limit: int = Field(default=10, ge=1, le=100)
    use_cache: bool | None = None

    def to_request(self) -> ProviderRequest:
        return ProviderRequest(
            query=self.query,
            geography=self.geography,
            language=self.language,
            limit=self.limit,
        )


class ProviderSearchResponse(BaseModel):
    result: ProviderResponse


class ProviderUsageSummaryResponse(BaseModel):
    summary: dict[str, Any]
