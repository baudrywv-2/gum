"""Live X API adapter tests (HTTP mocked — no real network / no secrets)."""

from __future__ import annotations

import json

import httpx

from packages.contracts.providers import ProviderMode, ProviderRequest
from providers.config import ProviderSettings
from providers.x_api import XApiProvider


def _settings(*, force_mock: bool, token: str | None) -> ProviderSettings:
    # Always set bearer explicitly so repo-root `.env` cannot leak into unit tests.
    payload: dict = {
        "GUM_FORCE_MOCK_PROVIDERS": force_mock,
        "X_API_BASE_URL": "https://api.x.com/2",
        "X_API_BEARER_TOKEN": token or "",
    }
    return ProviderSettings.model_validate(payload)


def _client_for(handler) -> httpx.Client:
    transport = httpx.MockTransport(handler)
    return httpx.Client(transport=transport, base_url="https://api.x.com")


def test_falls_back_to_mock_when_token_missing() -> None:
    provider = XApiProvider(settings=_settings(force_mock=False, token=None))
    result = provider.search(ProviderRequest(query="niche keyword"))
    assert result.mode is ProviderMode.MOCK
    assert result.claim_tag.value == "UNVERIFIED_CLAIM"
    assert result.raw.get("mocked") is True
    assert any("MOCK" in item.title for item in result.items)


def test_force_mock_overrides_configured_token() -> None:
    provider = XApiProvider(settings=_settings(force_mock=True, token="test-token"))
    assert provider.status().mode is ProviderMode.MOCK
    result = provider.search(ProviderRequest(query="invoice automation"))
    assert result.mode is ProviderMode.MOCK
    assert result.raw.get("mocked") is True


def test_live_search_maps_posts_with_measured_fact() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/tweets/search/recent")
        assert request.headers.get("Authorization") == "Bearer test-token"
        assert "freelancer" in str(request.url) and "invoicing" in str(request.url)
        body = {
            "data": [
                {
                    "id": "111",
                    "text": "Struggling with freelancer invoicing tools again",
                    "author_id": "42",
                    "created_at": "2026-11-10T12:00:00.000Z",
                    "lang": "en",
                    "public_metrics": {
                        "like_count": 3,
                        "retweet_count": 1,
                        "reply_count": 0,
                        "quote_count": 0,
                        "bookmark_count": 2,
                    },
                }
            ],
            "includes": {
                "users": [{"id": "42", "username": "acct", "name": "Acct"}]
            },
            "meta": {"result_count": 1, "newest_id": "111", "oldest_id": "111"},
        }
        return httpx.Response(200, json=body)

    provider = XApiProvider(
        settings=_settings(force_mock=False, token="test-token"),
        http_client=_client_for(handler),
    )
    status = provider.status()
    assert status.mode is ProviderMode.LIVE
    assert status.configured is True

    result = provider.search(ProviderRequest(query="freelancer invoicing", limit=5))
    assert result.mode is ProviderMode.LIVE
    assert result.claim_tag.value == "MEASURED_FACT"
    assert len(result.items) == 1
    item = result.items[0]
    assert item.claim_tag.value == "MEASURED_FACT"
    assert item.attributes.get("mocked") is False
    assert item.attributes.get("author") == "@acct"
    assert item.attributes.get("engagement") == {
        "likes": 3,
        "reposts": 1,
        "replies": 0,
        "quotes": 0,
        "bookmarks": 2,
    }
    assert item.attributes.get("public_metrics", {}).get("bookmark_count") == 2
    assert item.url and item.url.endswith("/111")
    assert result.raw.get("result_count") == 1
    assert result.raw.get("mocked") is False
    assert any("not purchase-intent" in line.lower() for line in result.limitations)


def test_auth_error_returns_unavailable_without_fake_items() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"title": "Unauthorized", "detail": "bad token"})

    provider = XApiProvider(
        settings=_settings(force_mock=False, token="bad-token"),
        http_client=_client_for(handler),
    )
    result = provider.search(ProviderRequest(query="anything"))
    assert result.mode is ProviderMode.UNAVAILABLE
    assert result.items == []
    assert result.raw.get("error") == "auth_error"
    assert result.raw.get("http_status") == 401
    assert any("No mock/synthetic" in line for line in result.limitations)


def test_rate_limit_returns_unavailable_without_fake_volume() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, json={"title": "Too Many Requests"})

    provider = XApiProvider(
        settings=_settings(force_mock=False, token="test-token"),
        http_client=_client_for(handler),
    )
    result = provider.search(ProviderRequest(query="anything"))
    assert result.mode is ProviderMode.UNAVAILABLE
    assert result.items == []
    assert result.raw.get("error") == "rate_limited"
    assert "429" in result.summary


def test_credits_depleted_returns_unavailable_without_fake_volume() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            402,
            json={
                "title": "Payment Required",
                "detail": "Credits depleted",
                "type": "https://api.x.com/2/problems/credits-depleted",
                "status": 402,
            },
        )

    provider = XApiProvider(
        settings=_settings(force_mock=False, token="test-token"),
        http_client=_client_for(handler),
    )
    result = provider.search(ProviderRequest(query="anything"))
    assert result.mode is ProviderMode.UNAVAILABLE
    assert result.items == []
    assert result.raw.get("error") == "credits_depleted"
    assert result.raw.get("http_status") == 402


def test_empty_live_results_are_honest_zero() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            content=json.dumps({"meta": {"result_count": 0}}).encode(),
            headers={"content-type": "application/json"},
        )

    provider = XApiProvider(
        settings=_settings(force_mock=False, token="test-token"),
        http_client=_client_for(handler),
    )
    result = provider.search(ProviderRequest(query="obscure niche xyzzy", limit=10))
    assert result.mode is ProviderMode.LIVE
    assert result.items == []
    assert result.raw.get("result_count") == 0
    assert result.claim_tag.value == "MEASURED_FACT"
