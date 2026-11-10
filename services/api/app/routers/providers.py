"""Provider status, search, and usage endpoints (Milestone 2)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.providers import (
    ProviderListResponse,
    ProviderSearchBody,
    ProviderSearchResponse,
    ProviderUsageSummaryResponse,
)
from packages.contracts.providers import ProviderName
from providers.config import get_provider_settings
from providers.registry import get_registry

router = APIRouter(prefix="/providers", tags=["providers"])


@router.get("", response_model=ProviderListResponse)
def list_providers() -> ProviderListResponse:
    registry = get_registry()
    settings = get_provider_settings()
    return ProviderListResponse(
        providers=registry.list_status(),
        force_mock=settings.force_mock_providers,
        cache=registry.cache.stats(),
    )


@router.get("/usage", response_model=ProviderUsageSummaryResponse)
def provider_usage() -> ProviderUsageSummaryResponse:
    return ProviderUsageSummaryResponse(summary=get_registry().usage.summary())


@router.post("/{provider_name}/search", response_model=ProviderSearchResponse)
def search_provider(
    provider_name: str, body: ProviderSearchBody
) -> ProviderSearchResponse:
    try:
        name = ProviderName(provider_name)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown provider: {provider_name}") from exc

    registry = get_registry()
    try:
        result = registry.search(
            name, body.to_request(), use_cache=body.use_cache
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ProviderSearchResponse(result=result)
