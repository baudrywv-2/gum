"""X (Twitter) API adapter — live recent-search when bearer configured; else mock."""

from __future__ import annotations

from typing import Any

import httpx

from packages.contracts.claim_tags import ClaimTag
from packages.contracts.providers import (
    ProviderCapability,
    ProviderMode,
    ProviderName,
    ProviderRequest,
    ProviderResponse,
    ProviderResultItem,
    ProviderStatus,
)
from providers.base import Provider, mock_response, utcnow
from providers.config import ProviderSettings, get_provider_settings


class XApiProvider(Provider):
    name = ProviderName.X_API
    capabilities = [ProviderCapability.SOCIAL_SEARCH]

    def __init__(
        self,
        settings: ProviderSettings | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.settings = settings or get_provider_settings()
        self._http_client = http_client

    def _should_mock(self) -> bool:
        return self.settings.should_mock(self.settings.x_api_configured())

    def status(self) -> ProviderStatus:
        configured = self.settings.x_api_configured()
        if self._should_mock():
            mode = ProviderMode.MOCK
            notes = (
                "Mocked until X_API_BEARER_TOKEN is set and GUM_FORCE_MOCK_PROVIDERS=false. "
                "X posts are discovery signals only — never proof of market size."
            )
        else:
            mode = ProviderMode.LIVE
            notes = (
                "Live X recent-search enabled (read-only). Posts are discovery signals "
                "only — not purchase-intent or market-size proof."
            )
        return ProviderStatus(
            name=self.name,
            mode=mode,
            configured=configured,
            capabilities=self.capabilities,
            notes=notes,
        )

    def search(self, request: ProviderRequest) -> ProviderResponse:
        if self._should_mock():
            return self._mock_search(request)
        return self._live_search(request)

    def _mock_search(self, request: ProviderRequest) -> ProviderResponse:
        items = [
            ProviderResultItem(
                title=f"[MOCK x_api] Frustrated with {request.query}",
                snippet=(
                    f"I hate how hard it is to find a good solution for {request.query}. "
                    "Wish there was something simpler that doesn't waste my time."
                ),
                url="https://x.com/example/status/0",
                claim_tag=ClaimTag.UNVERIFIED_CLAIM,
                attributes={
                    "author": "@mock_user",
                    "engagement": {
                        "likes": 0,
                        "reposts": 0,
                        "replies": 0,
                        "quotes": 0,
                        "bookmarks": 0,
                    },
                    "mocked": True,
                },
            ),
            ProviderResultItem(
                title=f"[MOCK x_api] InvoiceBot issue with {request.query}",
                snippet=(
                    f"Problem with InvoiceBot for {request.query}: too expensive "
                    "and it fails to cover basic exports. Missing a simple CSV feature."
                ),
                url="https://x.com/example/status/1",
                claim_tag=ClaimTag.UNVERIFIED_CLAIM,
                attributes={
                    "author": "@mock_user_2",
                    "engagement": {
                        "likes": 0,
                        "reposts": 0,
                        "replies": 0,
                        "quotes": 0,
                        "bookmarks": 0,
                    },
                    "mocked": True,
                    "mentioned_competitor": "InvoiceBot",
                },
            ),
        ]
        return mock_response(
            provider=self.name,
            request=request,
            summary=f"Mocked X recent-search for '{request.query}'",
            items=items[: request.limit],
            limitations=[
                "X API adapter returned MOCK data — posts are synthetic placeholders.",
                "No live X API request was made.",
                "Social signals are not purchase-intent proof.",
            ],
            raw={"adapter": "x_api", "mocked": True},
        )

    def _live_search(self, request: ProviderRequest) -> ProviderResponse:
        token = (self.settings.x_api_bearer_token or "").strip()
        if not token:
            # Token missing after status said live — fall back honestly to mock.
            return self._mock_search(request)

        # X recent-search requires max_results in [10, 100]; slice to request.limit after.
        max_results = max(10, min(100, max(request.limit, 10)))
        query = request.query.strip()
        if request.language:
            # Soft language preference; keep keyword intact if operator already present.
            lang = request.language.strip().lower()
            if lang and "lang:" not in query.lower():
                query = f"{query} lang:{lang}"

        base = self.settings.x_api_base_url.rstrip("/")
        url = f"{base}/tweets/search/recent"
        params = {
            "query": query,
            "max_results": max_results,
            "tweet.fields": "created_at,public_metrics,author_id,lang",
            "expansions": "author_id",
            "user.fields": "username,name",
        }
        headers = {"Authorization": f"Bearer {token}"}

        owns_client = self._http_client is None
        client = self._http_client or httpx.Client(timeout=30.0)
        try:
            response = client.get(url, params=params, headers=headers)
        except httpx.RequestError as exc:
            return self._unavailable_response(
                request=request,
                reason="network_error",
                detail=f"X API request failed before a response: {exc.__class__.__name__}",
                http_status=None,
            )
        finally:
            if owns_client:
                client.close()

        if response.status_code in (401, 403):
            return self._unavailable_response(
                request=request,
                reason="auth_error",
                detail=(
                    f"X API authentication/authorization failed "
                    f"(HTTP {response.status_code}). No results fabricated."
                ),
                http_status=response.status_code,
            )
        if response.status_code == 402:
            return self._unavailable_response(
                request=request,
                reason="credits_depleted",
                detail=(
                    "X API credits/payment required (HTTP 402). "
                    "No synthetic volume returned."
                ),
                http_status=402,
                raw_body=_safe_json(response),
            )
        if response.status_code == 429:
            return self._unavailable_response(
                request=request,
                reason="rate_limited",
                detail=(
                    "X API rate limit reached (HTTP 429). No synthetic volume returned."
                ),
                http_status=429,
            )
        if response.status_code >= 400:
            return self._unavailable_response(
                request=request,
                reason="http_error",
                detail=f"X API returned HTTP {response.status_code}. No results fabricated.",
                http_status=response.status_code,
                raw_body=_safe_json(response),
            )

        payload = _safe_json(response)
        users_by_id = _users_index(payload)
        tweets = payload.get("data") or []
        meta = payload.get("meta") or {}
        result_count = meta.get("result_count")
        if result_count is None:
            result_count = len(tweets)

        items: list[ProviderResultItem] = []
        for tweet in tweets[: request.limit]:
            tweet_id = str(tweet.get("id") or "")
            text = (tweet.get("text") or "").strip()
            author_id = str(tweet.get("author_id") or "")
            user = users_by_id.get(author_id, {})
            username = user.get("username")
            metrics = tweet.get("public_metrics") or {}
            title = text.split("\n", 1)[0][:120] or f"X post {tweet_id}"
            items.append(
                ProviderResultItem(
                    title=title,
                    snippet=text or None,
                    url=f"https://x.com/i/web/status/{tweet_id}" if tweet_id else None,
                    claim_tag=ClaimTag.MEASURED_FACT,
                    attributes={
                        "source": "x_api_recent_search",
                        "tweet_id": tweet_id or None,
                        "author_id": author_id or None,
                        "author": f"@{username}" if username else None,
                        "created_at": tweet.get("created_at"),
                        "lang": tweet.get("lang"),
                        "engagement": {
                            # X public_metrics on the post object. Keys missing
                            # from the API payload stay null (do not invent).
                            "likes": metrics.get("like_count"),
                            "reposts": metrics.get("retweet_count"),
                            "replies": metrics.get("reply_count"),
                            "quotes": metrics.get("quote_count"),
                            "bookmarks": metrics.get("bookmark_count"),
                        },
                        "public_metrics": metrics,
                        "mocked": False,
                        "claim_note": (
                            "MEASURED_FACT = post returned by X recent-search; "
                            "engagement counts are X public_metrics, not demand proof."
                        ),
                    },
                )
            )

        return ProviderResponse(
            provider=self.name,
            mode=ProviderMode.LIVE,
            query=request.query,
            summary=(
                f"Live X recent-search for '{request.query}': "
                f"{len(items)} item(s) returned (meta.result_count={result_count})."
            ),
            claim_tag=ClaimTag.MEASURED_FACT,
            fetched_at=utcnow(),
            cached=False,
            items=items,
            limitations=[
                "Live X recent-search covers roughly the last 7 days only.",
                "Result counts reflect this query window — not total market demand.",
                "Social posts are discovery signals, not purchase-intent proof.",
                "Engagement metrics are X public_metrics, not fabricated volume.",
            ],
            raw={
                "adapter": "x_api",
                "mocked": False,
                "mode": ProviderMode.LIVE.value,
                "http_status": response.status_code,
                "meta": meta,
                "result_count": result_count,
                "returned_items": len(items),
            },
        )

    def _unavailable_response(
        self,
        *,
        request: ProviderRequest,
        reason: str,
        detail: str,
        http_status: int | None,
        raw_body: dict[str, Any] | None = None,
    ) -> ProviderResponse:
        return ProviderResponse(
            provider=self.name,
            mode=ProviderMode.UNAVAILABLE,
            query=request.query,
            summary=f"X recent-search unavailable ({reason}): {detail}",
            claim_tag=ClaimTag.UNVERIFIED_CLAIM,
            fetched_at=utcnow(),
            cached=False,
            items=[],
            limitations=[
                detail,
                "No mock/synthetic posts substituted for this failure.",
                "Do not treat absence of results here as measured zero demand.",
            ],
            raw={
                "adapter": "x_api",
                "mocked": False,
                "mode": ProviderMode.UNAVAILABLE.value,
                "error": reason,
                "http_status": http_status,
                "body": raw_body or {},
            },
        )


def _safe_json(response: httpx.Response) -> dict[str, Any]:
    try:
        data = response.json()
    except ValueError:
        return {"non_json_body": True}
    return data if isinstance(data, dict) else {"value": data}


def _users_index(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    includes = payload.get("includes") or {}
    users = includes.get("users") or []
    out: dict[str, dict[str, Any]] = {}
    for user in users:
        user_id = str(user.get("id") or "")
        if user_id:
            out[user_id] = user
    return out
