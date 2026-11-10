"""YouTube Data API v3 adapter — live video search when key configured; else mock."""

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

DEFAULT_YOUTUBE_API_BASE_URL = "https://www.googleapis.com/youtube/v3"


class YouTubeProvider(Provider):
    name = ProviderName.YOUTUBE
    capabilities = [ProviderCapability.VIDEO_SEARCH, ProviderCapability.SOCIAL_SEARCH]

    def __init__(
        self,
        settings: ProviderSettings | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.settings = settings or get_provider_settings()
        self._http_client = http_client

    def _should_mock(self) -> bool:
        return self.settings.should_mock(self.settings.youtube_configured())

    def status(self) -> ProviderStatus:
        configured = self.settings.youtube_configured()
        if self._should_mock():
            mode = ProviderMode.MOCK
            notes = (
                "Mocked until YOUTUBE_API_KEY is set and GUM_FORCE_MOCK_PROVIDERS=false. "
                "Video results are discovery signals only — not demand proof."
            )
        else:
            mode = ProviderMode.LIVE
            notes = (
                "Live YouTube Data API v3 search enabled. View counts are observed "
                "public statistics — not purchase-intent or market-size proof."
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
                title=f"[MOCK youtube] How to handle {request.query}",
                snippet=(
                    f"Synthetic YouTube placeholder about {request.query}. "
                    "Not a real video result."
                ),
                url="https://www.youtube.com/watch?v=mock0000000",
                claim_tag=ClaimTag.UNVERIFIED_CLAIM,
                attributes={
                    "channel": "Mock Channel",
                    "views": None,
                    "mocked": True,
                },
            ),
            ProviderResultItem(
                title=f"[MOCK youtube] {request.query} tools compared",
                snippet=f"Synthetic comparison video stub for {request.query}.",
                url="https://www.youtube.com/watch?v=mock0000001",
                claim_tag=ClaimTag.UNVERIFIED_CLAIM,
                attributes={
                    "channel": "Mock Reviews",
                    "views": None,
                    "mocked": True,
                },
            ),
        ]
        return mock_response(
            provider=self.name,
            request=request,
            summary=f"Mocked YouTube search for '{request.query}'",
            items=items[: request.limit],
            limitations=[
                "YouTube adapter returned MOCK data — videos are synthetic placeholders.",
                "No YouTube Data API request was made.",
                "Video view counts are not purchase-intent proof.",
            ],
            raw={"adapter": "youtube", "mocked": True},
        )

    def _live_search(self, request: ProviderRequest) -> ProviderResponse:
        api_key = (self.settings.youtube_api_key or "").strip()
        if not api_key:
            return self._mock_search(request)

        base = (self.settings.youtube_api_base_url or DEFAULT_YOUTUBE_API_BASE_URL).rstrip(
            "/"
        )
        max_results = max(1, min(50, request.limit))
        search_params: dict[str, Any] = {
            "part": "snippet",
            "type": "video",
            "q": request.query,
            "maxResults": max_results,
            "key": api_key,
        }
        if request.language:
            # relevanceLanguage is ISO 639-1 (e.g. en)
            search_params["relevanceLanguage"] = request.language.strip().lower()[:2]
        if request.geography:
            # regionCode is ISO 3166-1 alpha-2
            search_params["regionCode"] = request.geography.strip().upper()[:2]

        owns_client = self._http_client is None
        client = self._http_client or httpx.Client(timeout=30.0)
        try:
            try:
                search_resp = client.get(f"{base}/search", params=search_params)
            except httpx.RequestError as exc:
                return self._unavailable_response(
                    request=request,
                    reason="network_error",
                    detail=(
                        "YouTube API request failed before a response: "
                        f"{exc.__class__.__name__}"
                    ),
                    http_status=None,
                )

            failure = _classify_youtube_failure(search_resp)
            if failure:
                reason, detail = failure
                return self._unavailable_response(
                    request=request,
                    reason=reason,
                    detail=detail,
                    http_status=search_resp.status_code,
                    raw_body=_safe_json(search_resp),
                )

            search_payload = _safe_json(search_resp)
            entries = search_payload.get("items") or []
            video_ids: list[str] = []
            for entry in entries:
                vid = ((entry.get("id") or {}).get("videoId")) or ""
                if vid:
                    video_ids.append(vid)

            stats_by_id: dict[str, dict[str, Any]] = {}
            videos_http_status: int | None = None
            if video_ids:
                # One cheap videos.list for statistics + channel confirmation.
                try:
                    videos_resp = client.get(
                        f"{base}/videos",
                        params={
                            "part": "statistics,snippet",
                            "id": ",".join(video_ids[:50]),
                            "key": api_key,
                        },
                    )
                    videos_http_status = videos_resp.status_code
                    # Stats enrichment is best-effort; search results still stand if it fails.
                    if videos_resp.status_code < 400:
                        for item in (_safe_json(videos_resp).get("items") or []):
                            vid = str(item.get("id") or "")
                            if vid:
                                stats_by_id[vid] = item
                except httpx.RequestError:
                    videos_http_status = None
        finally:
            if owns_client:
                client.close()

        items: list[ProviderResultItem] = []
        for entry in entries[: request.limit]:
            vid = ((entry.get("id") or {}).get("videoId")) or ""
            snippet = entry.get("snippet") or {}
            enriched = stats_by_id.get(vid) or {}
            enriched_snippet = enriched.get("snippet") or snippet
            statistics = enriched.get("statistics") or {}
            title = (snippet.get("title") or "").strip() or f"YouTube video {vid}"
            description = (snippet.get("description") or "").strip() or None
            channel = (
                enriched_snippet.get("channelTitle")
                or snippet.get("channelTitle")
            )
            views_raw = statistics.get("viewCount")
            try:
                views = int(views_raw) if views_raw is not None else None
            except (TypeError, ValueError):
                views = None
            items.append(
                ProviderResultItem(
                    title=title,
                    snippet=description,
                    url=f"https://www.youtube.com/watch?v={vid}" if vid else None,
                    claim_tag=ClaimTag.MEASURED_FACT,
                    attributes={
                        "source": "youtube_data_api_v3",
                        "video_id": vid or None,
                        "channel": channel,
                        "channel_id": snippet.get("channelId")
                        or enriched_snippet.get("channelId"),
                        "published_at": snippet.get("publishedAt"),
                        "views": views,
                        "like_count": _int_or_none(statistics.get("likeCount")),
                        "comment_count": _int_or_none(statistics.get("commentCount")),
                        "mocked": False,
                        "claim_note": (
                            "MEASURED_FACT = video returned by YouTube search "
                            "(+ public statistics when available); not demand proof."
                        ),
                    },
                )
            )

        return ProviderResponse(
            provider=self.name,
            mode=ProviderMode.LIVE,
            query=request.query,
            summary=(
                f"Live YouTube search for '{request.query}': "
                f"{len(items)} video(s) returned."
            ),
            claim_tag=ClaimTag.MEASURED_FACT,
            fetched_at=utcnow(),
            cached=False,
            items=items,
            limitations=[
                "Live YouTube Data API v3 search — discovery signals only.",
                "View/like/comment counts are public statistics, not purchase-intent proof.",
                "Do not treat video volume or views as measured market demand.",
            ],
            raw={
                "adapter": "youtube",
                "mocked": False,
                "mode": ProviderMode.LIVE.value,
                "http_status": search_resp.status_code,
                "videos_http_status": videos_http_status,
                "page_info": search_payload.get("pageInfo") or {},
                "returned_items": len(items),
                "stats_enriched": len(stats_by_id),
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
            summary=f"YouTube search unavailable ({reason}): {detail}",
            claim_tag=ClaimTag.UNVERIFIED_CLAIM,
            fetched_at=utcnow(),
            cached=False,
            items=[],
            limitations=[
                detail,
                "No mock/synthetic videos substituted for this failure.",
                "Do not treat absence of results here as measured zero demand.",
            ],
            raw={
                "adapter": "youtube",
                "mocked": False,
                "mode": ProviderMode.UNAVAILABLE.value,
                "error": reason,
                "http_status": http_status,
                "body": raw_body or {},
            },
        )


def _int_or_none(value: Any) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _safe_json(response: httpx.Response) -> dict[str, Any]:
    try:
        data = response.json()
    except ValueError:
        return {"non_json_body": True}
    return data if isinstance(data, dict) else {"value": data}


def _classify_youtube_failure(
    response: httpx.Response,
) -> tuple[str, str] | None:
    if response.status_code in (401, 403):
        payload = _safe_json(response)
        err = (payload.get("error") or {}) if isinstance(payload.get("error"), dict) else {}
        message = str(err.get("message") or payload.get("error") or "").strip()
        reasons = {str(e.get("reason") or "") for e in (err.get("errors") or [])}
        # Quota often arrives as HTTP 403 with reason dailyLimitExceeded / quotaExceeded.
        if reasons & {
            "dailyLimitExceeded",
            "quotaExceeded",
            "rateLimitExceeded",
            "userRateLimitExceeded",
        } or "quota" in message.lower():
            return (
                "quota_error",
                (
                    f"YouTube API quota/rate limit (HTTP {response.status_code}"
                    + (f": {message}" if message else "")
                    + "). No synthetic volume returned."
                ),
            )
        return (
            "auth_error",
            (
                f"YouTube API authentication/authorization failed "
                f"(HTTP {response.status_code}"
                + (f": {message}" if message else "")
                + "). No results fabricated."
            ),
        )
    if response.status_code == 429:
        return (
            "rate_limited",
            "YouTube API rate limit reached (HTTP 429). No synthetic volume returned.",
        )
    if response.status_code >= 400:
        payload = _safe_json(response)
        err = (payload.get("error") or {}) if isinstance(payload.get("error"), dict) else {}
        message = str(err.get("message") or "").strip()
        return (
            "http_error",
            (
                f"YouTube API returned HTTP {response.status_code}"
                + (f": {message}" if message else "")
                + ". No results fabricated."
            ),
        )
    return None
