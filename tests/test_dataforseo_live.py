"""DataForSEO SERP + keyword overview tests (HTTP mocked — no secrets / no network)."""

from __future__ import annotations

import httpx

from packages.contracts.providers import ProviderMode, ProviderName, ProviderRequest
from providers.config import ProviderSettings
from providers.dataforseo_serp import DataForSeoSerpProvider
from providers.google_ads import GoogleAdsProvider
from providers.registry import ProviderRegistry, build_serp_provider
from providers.serp import SerpProvider


def _settings(**overrides) -> ProviderSettings:
    base = {
        "GUM_FORCE_MOCK_PROVIDERS": False,
        "SERP_PROVIDER": "dataforseo",
        "DATAFORSEO_LOGIN": "",
        "DATAFORSEO_PASSWORD": "",
        "SERPAPI_API_KEY": "",
        "DATAFORSEO_BASE_URL": "https://api.dataforseo.com",
    }
    base.update(overrides)
    return ProviderSettings.model_validate(base)


def _client_for(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_mock_fallback_when_credentials_missing() -> None:
    provider = DataForSeoSerpProvider(
        settings=_settings(DATAFORSEO_LOGIN="", DATAFORSEO_PASSWORD="")
    )
    result = provider.search(ProviderRequest(query="niche"))
    assert result.mode is ProviderMode.MOCK
    assert result.claim_tag.value == "UNVERIFIED_CLAIM"
    assert result.raw.get("backend") == "dataforseo"


def test_registry_uses_serpapi_by_default() -> None:
    settings = _settings(SERP_PROVIDER="serpapi", SERPAPI_API_KEY="k")
    assert isinstance(build_serp_provider(settings), SerpProvider)
    registry = ProviderRegistry(settings=settings)
    assert registry.get(ProviderName.SERP).__class__ is SerpProvider


def test_registry_switches_to_dataforseo() -> None:
    settings = _settings(
        SERP_PROVIDER="dataforseo",
        DATAFORSEO_LOGIN="user",
        DATAFORSEO_PASSWORD="pass",
    )
    assert isinstance(build_serp_provider(settings), DataForSeoSerpProvider)


def test_live_serp_maps_organic_measured_fact() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/v3/serp/google/organic/live/regular")
        assert request.headers.get("Authorization", "").startswith("Basic ")
        # Ensure we never echo credentials in assertions beyond scheme.
        return httpx.Response(
            200,
            json={
                "status_code": 20000,
                "status_message": "Ok.",
                "cost": 0.002,
                "tasks": [
                    {
                        "status_code": 20000,
                        "result": [
                            {
                                "items": [
                                    {
                                        "type": "organic",
                                        "rank_group": 1,
                                        "rank_absolute": 1,
                                        "title": "Invoicing tools",
                                        "description": "CSV export help",
                                        "url": "https://example.com/a",
                                        "domain": "example.com",
                                    }
                                ]
                            }
                        ],
                    }
                ],
            },
        )

    provider = DataForSeoSerpProvider(
        settings=_settings(DATAFORSEO_LOGIN="user", DATAFORSEO_PASSWORD="pass"),
        http_client=_client_for(handler),
    )
    assert provider.status().mode is ProviderMode.LIVE
    result = provider.search(ProviderRequest(query="invoicing", limit=5))
    assert result.mode is ProviderMode.LIVE
    assert result.claim_tag.value == "MEASURED_FACT"
    assert len(result.items) == 1
    assert result.items[0].attributes.get("backend") == "dataforseo"
    assert result.raw.get("mocked") is False


def test_auth_error_unavailable_no_fake_volume() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "status_code": 40102,
                "status_message": "Unauthorized.",
                "tasks": [],
            },
        )

    provider = DataForSeoSerpProvider(
        settings=_settings(DATAFORSEO_LOGIN="bad", DATAFORSEO_PASSWORD="bad"),
        http_client=_client_for(handler),
    )
    result = provider.search(ProviderRequest(query="x"))
    assert result.mode is ProviderMode.UNAVAILABLE
    assert result.items == []
    assert result.raw.get("error") == "auth_error"


def test_balance_error_unavailable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "status_code": 40204,
                "status_message": "Access denied. Visit Plans page to modify your limits.",
                "tasks": [],
            },
        )

    provider = DataForSeoSerpProvider(
        settings=_settings(DATAFORSEO_LOGIN="user", DATAFORSEO_PASSWORD="pass"),
        http_client=_client_for(handler),
    )
    result = provider.search(ProviderRequest(query="x"))
    assert result.mode is ProviderMode.UNAVAILABLE
    assert result.items == []
    assert result.raw.get("error") == "balance_error"


def test_keyword_overview_live_measured_fact() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "keyword_overview" in str(request.url)
        return httpx.Response(
            200,
            json={
                "status_code": 20000,
                "tasks": [
                    {
                        "status_code": 20000,
                        "result": [
                            {
                                "items": [
                                    {
                                        "keyword": "invoicing",
                                        "keyword_info": {
                                            "search_volume": 12100,
                                            "competition": 0.4,
                                            "competition_level": "MEDIUM",
                                            "cpc": 1.2,
                                        },
                                    }
                                ]
                            }
                        ],
                    }
                ],
            },
        )

    provider = GoogleAdsProvider(
        settings=_settings(DATAFORSEO_LOGIN="user", DATAFORSEO_PASSWORD="pass"),
        http_client=_client_for(handler),
    )
    assert provider.status().mode is ProviderMode.LIVE
    result = provider.search(ProviderRequest(query="invoicing", limit=3))
    assert result.mode is ProviderMode.LIVE
    assert result.claim_tag.value == "MEASURED_FACT"
    assert result.items[0].attributes.get("avg_monthly_searches") == 12100
    assert result.raw.get("backend") == "dataforseo"


def test_force_mock_blocks_dataforseo_live() -> None:
    provider = DataForSeoSerpProvider(
        settings=_settings(
            GUM_FORCE_MOCK_PROVIDERS=True,
            DATAFORSEO_LOGIN="user",
            DATAFORSEO_PASSWORD="pass",
        )
    )
    assert provider.status().mode is ProviderMode.MOCK
    result = provider.search(ProviderRequest(query="x"))
    assert result.mode is ProviderMode.MOCK
