"""Milestone 2 provider infrastructure tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from packages.contracts.providers import ProviderMode, ProviderName, ProviderRequest
from providers.cache import ProviderCache
from providers.config import reset_provider_settings
from providers.google_ads import GoogleAdsProvider
from providers.registry import ProviderRegistry, reset_registry
from providers.serp import SerpProvider
from providers.usage import UsageTracker
from providers.x_api import XApiProvider


def test_all_named_adapters_are_mocked() -> None:
    registry = ProviderRegistry()
    statuses = {s.name: s for s in registry.list_status()}
    for name in (
        ProviderName.MOCK,
        ProviderName.GOOGLE_ADS,
        ProviderName.GOOGLE_TRENDS,
        ProviderName.SERP,
        ProviderName.X_API,
        ProviderName.YOUTUBE,
    ):
        assert name in statuses
        assert statuses[name].mode is ProviderMode.MOCK


def test_google_serp_x_stubs_mark_limitations() -> None:
    request = ProviderRequest(query="invoice automation")
    for provider in (GoogleAdsProvider(), SerpProvider(), XApiProvider()):
        result = provider.search(request)
        assert result.mode is ProviderMode.MOCK
        assert result.claim_tag.value == "UNVERIFIED_CLAIM"
        assert result.limitations
        assert any("stub" in line.lower() or "mock" in line.lower() for line in result.limitations)
        assert result.raw.get("mocked") is True
        assert all(
            "MOCK" in item.title or item.attributes.get("mocked") for item in result.items
        )


def test_cache_hit_and_usage_tracking() -> None:
    cache = ProviderCache(default_ttl_seconds=60)
    usage = UsageTracker()
    registry = ProviderRegistry(cache=cache, usage=usage)
    request = ProviderRequest(query="underserved niches")

    first = registry.search(ProviderName.SERP, request)
    second = registry.search(ProviderName.SERP, request)

    assert first.cached is False
    assert second.cached is True
    assert cache.stats()["hits"] == 1
    summary = usage.summary()
    assert summary["total_calls"] == 2
    assert summary["by_provider"]["serp"]["cache_hits"] == 1
    # Mock mode → no billable units
    assert summary["total_estimated_cost_usd"] == 0.0


def test_providers_api_list_and_search(client: TestClient) -> None:
    reset_provider_settings()
    reset_registry()

    listed = client.get("/providers")
    assert listed.status_code == 200
    body = listed.json()
    assert body["force_mock"] is True
    names = {p["name"] for p in body["providers"]}
    assert {"mock", "google_ads", "google_trends", "serp", "x_api", "youtube"} <= names
    assert all(p["mode"] == "mock" for p in body["providers"])

    search = client.post(
        "/providers/google_ads/search",
        json={"query": "local service gaps", "limit": 2},
    )
    assert search.status_code == 200
    result = search.json()["result"]
    assert result["provider"] == "google_ads"
    assert result["mode"] == "mock"
    assert result["cached"] is False

    cached = client.post(
        "/providers/google_ads/search",
        json={"query": "local service gaps", "limit": 2},
    )
    assert cached.json()["result"]["cached"] is True

    usage = client.get("/providers/usage")
    assert usage.status_code == 200
    assert usage.json()["summary"]["total_calls"] >= 2


def test_unknown_provider_returns_404(client: TestClient) -> None:
    response = client.post(
        "/providers/not_a_provider/search",
        json={"query": "x"},
    )
    assert response.status_code == 404
