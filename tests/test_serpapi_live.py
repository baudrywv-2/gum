"""SerpAPI SERP + Trends adapter tests (HTTP mocked — no secrets / no network)."""

from __future__ import annotations

import httpx

from packages.contracts.providers import ProviderMode, ProviderRequest
from providers.config import ProviderSettings
from providers.google_trends import GoogleTrendsProvider
from providers.serp import SerpProvider


def _settings(*, force_mock: bool, key: str | None) -> ProviderSettings:
    return ProviderSettings.model_validate(
        {
            "GUM_FORCE_MOCK_PROVIDERS": force_mock,
            "SERPAPI_API_KEY": key or "",
            "SERP_API_BASE_URL": "https://serpapi.com",
        }
    )


def _client_for(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_serp_falls_back_to_mock_when_key_missing() -> None:
    provider = SerpProvider(settings=_settings(force_mock=False, key=None))
    result = provider.search(ProviderRequest(query="niche keyword"))
    assert result.mode is ProviderMode.MOCK
    assert result.claim_tag.value == "UNVERIFIED_CLAIM"
    assert result.raw.get("mocked") is True
    assert result.items


def test_trends_falls_back_to_mock_when_key_missing() -> None:
    provider = GoogleTrendsProvider(settings=_settings(force_mock=False, key=None))
    result = provider.search(ProviderRequest(query="niche keyword"))
    assert result.mode is ProviderMode.MOCK
    assert result.claim_tag.value == "UNVERIFIED_CLAIM"
    assert result.raw.get("mocked") is True


def test_force_mock_overrides_configured_key() -> None:
    for cls in (SerpProvider, GoogleTrendsProvider):
        provider = cls(settings=_settings(force_mock=True, key="test-key"))
        assert provider.status().mode is ProviderMode.MOCK
        result = provider.search(ProviderRequest(query="invoice automation"))
        assert result.mode is ProviderMode.MOCK
        assert result.raw.get("mocked") is True


def test_live_serp_maps_organic_with_measured_fact() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "serpapi.com" in str(request.url)
        assert "engine=google" in str(request.url)
        assert "api_key=test-key" in str(request.url)
        return httpx.Response(
            200,
            json={
                "organic_results": [
                    {
                        "position": 1,
                        "title": "Freelancer invoicing tools",
                        "link": "https://example.com/tools",
                        "snippet": "Compare CSV export options",
                        "displayed_link": "https://example.com",
                    }
                ],
                "search_metadata": {"status": "Success"},
            },
        )

    provider = SerpProvider(
        settings=_settings(force_mock=False, key="test-key"),
        http_client=_client_for(handler),
    )
    assert provider.status().mode is ProviderMode.LIVE
    result = provider.search(ProviderRequest(query="freelancer invoicing", limit=5))
    assert result.mode is ProviderMode.LIVE
    assert result.claim_tag.value == "MEASURED_FACT"
    assert len(result.items) == 1
    assert result.items[0].claim_tag.value == "MEASURED_FACT"
    assert result.items[0].attributes.get("mocked") is False
    assert result.items[0].url == "https://example.com/tools"
    assert result.raw.get("mocked") is False


def test_live_trends_maps_timeseries_with_measured_fact() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "engine=google_trends" in str(request.url)
        assert "api_key=test-key" in str(request.url)
        return httpx.Response(
            200,
            json={
                "interest_over_time": {
                    "timeline_data": [
                        {
                            "date": "Jan 1, 2026",
                            "timestamp": "1",
                            "values": [{"query": "q", "value": "12", "extracted_value": 12}],
                        },
                        {
                            "date": "Feb 1, 2026",
                            "timestamp": "2",
                            "values": [{"query": "q", "value": "18", "extracted_value": 18}],
                        },
                    ],
                    "averages": [{"query": "q", "value": 15}],
                },
                "search_metadata": {"status": "Success"},
            },
        )

    provider = GoogleTrendsProvider(
        settings=_settings(force_mock=False, key="test-key"),
        http_client=_client_for(handler),
    )
    assert provider.status().mode is ProviderMode.LIVE
    result = provider.search(ProviderRequest(query="freelancer invoicing", limit=1))
    assert result.mode is ProviderMode.LIVE
    assert result.claim_tag.value == "MEASURED_FACT"
    assert len(result.items) == 1
    assert result.items[0].attributes.get("interest_over_time") == [12, 18]
    assert result.items[0].attributes.get("mocked") is False
    assert result.raw.get("point_count") == 2


def test_serp_auth_error_unavailable_no_fake_items() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "Invalid API key."})

    provider = SerpProvider(
        settings=_settings(force_mock=False, key="bad"),
        http_client=_client_for(handler),
    )
    result = provider.search(ProviderRequest(query="x"))
    assert result.mode is ProviderMode.UNAVAILABLE
    assert result.items == []
    assert result.raw.get("error") == "auth_error"


def test_trends_quota_error_in_body_unavailable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"error": "Your account has run out of searches."},
        )

    provider = GoogleTrendsProvider(
        settings=_settings(force_mock=False, key="test-key"),
        http_client=_client_for(handler),
    )
    result = provider.search(ProviderRequest(query="x"))
    assert result.mode is ProviderMode.UNAVAILABLE
    assert result.items == []
    assert result.raw.get("error") == "quota_error"


def test_trends_no_results_is_live_empty_not_fake_demand() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"error": "Google Trends hasn't returned any results for this query."},
        )

    provider = GoogleTrendsProvider(
        settings=_settings(force_mock=False, key="test-key"),
        http_client=_client_for(handler),
    )
    result = provider.search(ProviderRequest(query="obscure niche xyz"))
    assert result.mode is ProviderMode.LIVE
    assert result.claim_tag.value == "MEASURED_FACT"
    assert len(result.items) == 1
    assert result.items[0].attributes.get("point_count") == 0
    assert result.raw.get("empty_reason") == "trends_no_results"
    assert result.raw.get("mocked") is False


def test_legacy_serp_api_key_alias_still_configures() -> None:
    settings = ProviderSettings.model_validate(
        {
            "GUM_FORCE_MOCK_PROVIDERS": True,
            "SERP_API_KEY": "legacy-key",
        }
    )
    assert settings.serp_configured() is True
    assert settings.serp_api_key == "legacy-key"
