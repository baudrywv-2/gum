"""YouTube Data API v3 adapter tests (HTTP mocked — no secrets / no network)."""

from __future__ import annotations

import httpx

from packages.contracts.providers import ProviderMode, ProviderRequest
from providers.config import ProviderSettings
from providers.youtube import YouTubeProvider


def _settings(*, force_mock: bool, key: str | None) -> ProviderSettings:
    return ProviderSettings.model_validate(
        {
            "GUM_FORCE_MOCK_PROVIDERS": force_mock,
            "YOUTUBE_API_KEY": key or "",
            "YOUTUBE_API_BASE_URL": "https://www.googleapis.com/youtube/v3",
        }
    )


def _client_for(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_falls_back_to_mock_when_key_missing() -> None:
    provider = YouTubeProvider(settings=_settings(force_mock=False, key=None))
    result = provider.search(ProviderRequest(query="niche keyword"))
    assert result.mode is ProviderMode.MOCK
    assert result.claim_tag.value == "UNVERIFIED_CLAIM"
    assert result.raw.get("mocked") is True
    assert any("MOCK" in item.title for item in result.items)


def test_force_mock_overrides_configured_key() -> None:
    provider = YouTubeProvider(settings=_settings(force_mock=True, key="test-key"))
    assert provider.status().mode is ProviderMode.MOCK
    result = provider.search(ProviderRequest(query="invoice automation"))
    assert result.mode is ProviderMode.MOCK
    assert result.raw.get("mocked") is True


def test_live_search_maps_videos_with_measured_fact_and_views() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("/search"):
            assert "key=test-key" in str(request.url)
            assert "type=video" in str(request.url)
            return httpx.Response(
                200,
                json={
                    "items": [
                        {
                            "id": {"videoId": "abc123"},
                            "snippet": {
                                "title": "Freelancer invoicing tips",
                                "description": "How to invoice clients",
                                "channelTitle": "Finance Channel",
                                "channelId": "ch1",
                                "publishedAt": "2026-01-01T00:00:00Z",
                            },
                        }
                    ],
                    "pageInfo": {"totalResults": 1, "resultsPerPage": 1},
                },
            )
        if path.endswith("/videos"):
            assert "id=abc123" in str(request.url)
            return httpx.Response(
                200,
                json={
                    "items": [
                        {
                            "id": "abc123",
                            "snippet": {
                                "title": "Freelancer invoicing tips",
                                "channelTitle": "Finance Channel",
                                "channelId": "ch1",
                            },
                            "statistics": {
                                "viewCount": "12345",
                                "likeCount": "10",
                                "commentCount": "2",
                            },
                        }
                    ]
                },
            )
        return httpx.Response(404, json={"error": {"message": "unexpected path"}})

    provider = YouTubeProvider(
        settings=_settings(force_mock=False, key="test-key"),
        http_client=_client_for(handler),
    )
    assert provider.status().mode is ProviderMode.LIVE
    result = provider.search(ProviderRequest(query="freelancer invoicing", limit=5))
    assert result.mode is ProviderMode.LIVE
    assert result.claim_tag.value == "MEASURED_FACT"
    assert len(result.items) == 1
    item = result.items[0]
    assert item.claim_tag.value == "MEASURED_FACT"
    assert item.attributes.get("mocked") is False
    assert item.attributes.get("views") == 12345
    assert item.attributes.get("channel") == "Finance Channel"
    assert item.url and item.url.endswith("abc123")
    assert result.raw.get("stats_enriched") == 1


def test_auth_error_unavailable_no_fake_items() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            403,
            json={
                "error": {
                    "code": 403,
                    "message": "API key not valid.",
                    "errors": [{"reason": "badRequest"}],
                }
            },
        )

    provider = YouTubeProvider(
        settings=_settings(force_mock=False, key="bad"),
        http_client=_client_for(handler),
    )
    result = provider.search(ProviderRequest(query="x"))
    assert result.mode is ProviderMode.UNAVAILABLE
    assert result.items == []
    assert result.raw.get("error") == "auth_error"


def test_quota_error_unavailable_no_fake_volume() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            403,
            json={
                "error": {
                    "code": 403,
                    "message": "The request cannot be completed because you have exceeded your quota.",
                    "errors": [{"reason": "quotaExceeded"}],
                }
            },
        )

    provider = YouTubeProvider(
        settings=_settings(force_mock=False, key="test-key"),
        http_client=_client_for(handler),
    )
    result = provider.search(ProviderRequest(query="x"))
    assert result.mode is ProviderMode.UNAVAILABLE
    assert result.items == []
    assert result.raw.get("error") == "quota_error"
