"""Google Trends adapter — live via SerpAPI google_trends when configured; else mock."""

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
from providers.serpapi_http import (
    DEFAULT_SERPAPI_BASE_URL,
    classify_serpapi_failure,
    safe_json,
    serpapi_get,
    unavailable_response,
)


class GoogleTrendsProvider(Provider):
    name = ProviderName.GOOGLE_TRENDS
    capabilities = [ProviderCapability.TREND_INTEREST]

    def __init__(
        self,
        settings: ProviderSettings | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.settings = settings or get_provider_settings()
        self._http_client = http_client

    def _configured(self) -> bool:
        # Same SerpAPI key as organic SERP; optional GOOGLE_TRENDS_ENABLED stays informational.
        return self.settings.serp_configured()

    def _should_mock(self) -> bool:
        return self.settings.should_mock(self._configured())

    def status(self) -> ProviderStatus:
        configured = self._configured()
        if self._should_mock():
            mode = ProviderMode.MOCK
            notes = (
                "Mocked until SERPAPI_API_KEY is set and GUM_FORCE_MOCK_PROVIDERS=false. "
                "Interest values while mocked are synthetic placeholders."
            )
        else:
            mode = ProviderMode.LIVE
            notes = (
                "Live Google Trends interest-over-time via SerpAPI. Values are a "
                "relative 0–100 index — not absolute demand or purchase volume."
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
                title=f"[MOCK google_trends] interest: {request.query}",
                snippet="Synthetic interest series — not measured Trends data.",
                claim_tag=ClaimTag.UNVERIFIED_CLAIM,
                attributes={
                    "interest_over_time": [12, 18, 15, 22, 19],
                    "mocked": True,
                },
            )
        ]
        return mock_response(
            provider=self.name,
            request=request,
            summary=f"Mocked Google Trends interest for '{request.query}'",
            items=items[: request.limit],
            limitations=[
                "Google Trends adapter returned MOCK data — interest is fabricated.",
                "No SerpAPI Trends request was made.",
                "Relative interest is not purchase-intent proof.",
            ],
            raw={"adapter": "google_trends", "mocked": True},
        )

    def _live_search(self, request: ProviderRequest) -> ProviderResponse:
        api_key = (self.settings.serp_api_key or "").strip()
        if not api_key:
            return self._mock_search(request)

        base = (self.settings.serp_api_base_url or DEFAULT_SERPAPI_BASE_URL).strip()
        params: dict[str, Any] = {
            "engine": "google_trends",
            "q": request.query,
            "data_type": "TIMESERIES",
        }
        if request.geography:
            params["geo"] = request.geography.strip().upper()
        # Prefer a bounded recent window to keep responses cheap/small.
        params["date"] = (request.metadata or {}).get("date") or "today 12-m"

        owns_client = self._http_client is None
        client = self._http_client or httpx.Client(timeout=45.0)
        try:
            try:
                response = serpapi_get(
                    client=client, base_url=base, api_key=api_key, params=params
                )
            except httpx.RequestError as exc:
                return unavailable_response(
                    provider=self.name,
                    request=request,
                    reason="network_error",
                    detail=(
                        f"SerpAPI Trends request failed before a response: "
                        f"{exc.__class__.__name__}"
                    ),
                    http_status=None,
                )
        finally:
            if owns_client:
                client.close()

        payload = safe_json(response)
        error_text = str(payload.get("error") or "").strip()
        # SerpAPI often returns HTTP 200 + error when Trends has no series for a niche query.
        # Treat that as an honest live empty observation — not auth/quota failure.
        no_trends_data = "hasn't returned any results" in error_text.lower()
        if not no_trends_data:
            failure = classify_serpapi_failure(
                http_status=response.status_code, payload=payload
            )
            if failure:
                reason, detail = failure
                return unavailable_response(
                    provider=self.name,
                    request=request,
                    reason=reason,
                    detail=detail,
                    http_status=response.status_code,
                    raw_body={"error": payload.get("error")}
                    if payload.get("error")
                    else {},
                )

        interest = payload.get("interest_over_time") or {}
        timeline = interest.get("timeline_data") or []
        series: list[dict[str, Any]] = []
        values_only: list[int | float | None] = []
        for point in timeline:
            values = point.get("values") or []
            extracted = None
            if values:
                extracted = values[0].get("extracted_value")
                if extracted is None:
                    raw_val = values[0].get("value")
                    try:
                        extracted = int(str(raw_val).replace(",", "").replace("<", ""))
                    except (TypeError, ValueError):
                        extracted = None
            series.append(
                {
                    "date": point.get("date"),
                    "timestamp": point.get("timestamp"),
                    "extracted_value": extracted,
                }
            )
            values_only.append(extracted)

        averages = interest.get("averages") or []
        avg_value = None
        if averages:
            avg_value = averages[0].get("value")

        if no_trends_data and not series:
            items = [
                ProviderResultItem(
                    title=f"Google Trends: no series for {request.query}",
                    snippet=(
                        "SerpAPI reported that Google Trends returned no results "
                        "for this query window/geo."
                    ),
                    claim_tag=ClaimTag.MEASURED_FACT,
                    attributes={
                        "source": "serpapi_google_trends",
                        "data_type": "TIMESERIES",
                        "interest_over_time": [],
                        "timeline": [],
                        "point_count": 0,
                        "geo": params.get("geo"),
                        "date_range": params.get("date"),
                        "mocked": False,
                        "empty_reason": "trends_no_results",
                        "claim_note": (
                            "MEASURED_FACT = SerpAPI/Trends reported no series; "
                            "this is not fabricated zero demand."
                        ),
                    },
                )
            ]
            summary = (
                f"Live SerpAPI Google Trends for '{request.query}': "
                "no timeline data returned for this query/window."
            )
        else:
            items = [
                ProviderResultItem(
                    title=f"Google Trends interest: {request.query}",
                    snippet=(
                        f"SerpAPI interest-over-time series with {len(series)} point(s)"
                        + (f"; average={avg_value}" if avg_value is not None else "")
                        + "."
                    ),
                    claim_tag=ClaimTag.MEASURED_FACT,
                    attributes={
                        "source": "serpapi_google_trends",
                        "data_type": "TIMESERIES",
                        "interest_over_time": values_only,
                        "timeline": series[: max(request.limit * 5, 24)],
                        "average": avg_value,
                        "point_count": len(series),
                        "geo": params.get("geo"),
                        "date_range": params.get("date"),
                        "mocked": False,
                        "claim_note": (
                            "MEASURED_FACT = values returned by SerpAPI Google Trends; "
                            "index is relative 0–100, not absolute demand."
                        ),
                    },
                )
            ]
            summary = (
                f"Live SerpAPI Google Trends for '{request.query}': "
                f"{len(series)} timeline point(s)."
            )

        return ProviderResponse(
            provider=self.name,
            mode=ProviderMode.LIVE,
            query=request.query,
            summary=summary,
            claim_tag=ClaimTag.MEASURED_FACT,
            fetched_at=utcnow(),
            cached=False,
            items=items[: request.limit],
            limitations=[
                "Live Google Trends via SerpAPI — relative interest index (0–100).",
                "Trends interest is not search-volume dollars or purchase-intent proof.",
                "Do not fabricate demand from a relative index alone.",
                *(
                    [
                        "Google Trends returned no series for this query/window — "
                        "absence is not measured zero market demand."
                    ]
                    if no_trends_data and not series
                    else []
                ),
            ],
            raw={
                "adapter": "google_trends",
                "mocked": False,
                "mode": ProviderMode.LIVE.value,
                "http_status": response.status_code,
                "engine": "google_trends",
                "point_count": len(series),
                "returned_items": len(items[: request.limit]),
                "empty_reason": "trends_no_results"
                if no_trends_data and not series
                else None,
                "search_metadata": payload.get("search_metadata") or {},
            },
        )
