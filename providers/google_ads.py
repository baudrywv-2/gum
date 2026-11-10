"""Keyword ideas adapter — mock by default; live via DataForSEO Keyword Overview when configured."""

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
from providers.dataforseo_http import (
    DEFAULT_DATAFORSEO_BASE_URL,
    classify_dataforseo_failure,
    dataforseo_post,
    resolve_language_code,
    resolve_location_code,
    safe_json,
    unavailable_response,
)


class GoogleAdsProvider(Provider):
    """Keyword data for GUM.

    Native Google Ads Keyword Planner remains stubbed. When DataForSEO credentials
    are present and force-mock is off, live keyword overview metrics are fetched
    from DataForSEO Labs (labeled MEASURED_FACT as observed API payload; volumes
    are still provider estimates, not purchase proof).
    """

    name = ProviderName.GOOGLE_ADS
    capabilities = [ProviderCapability.KEYWORD_IDEAS]

    def __init__(
        self,
        settings: ProviderSettings | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.settings = settings or get_provider_settings()
        self._http_client = http_client

    def _live_via_dataforseo(self) -> bool:
        return self.settings.dataforseo_configured() and not self.settings.should_mock(
            True
        )

    def status(self) -> ProviderStatus:
        dfs = self.settings.dataforseo_configured()
        native = self.settings.google_ads_configured()
        configured = dfs or native
        if self._live_via_dataforseo():
            mode = ProviderMode.LIVE
            notes = (
                "Live keyword overview via DataForSEO Labs. Search volumes are "
                "provider estimates (Google Ads–derived) — not purchase-intent proof. "
                "Native Google Ads client remains stubbed."
            )
        elif native and not self.settings.force_mock_providers:
            mode = ProviderMode.MOCK
            notes = (
                "Native Google Ads credentials detected but live Keyword Planner "
                "client is not implemented — no Google Ads API calls."
            )
        else:
            mode = ProviderMode.MOCK
            notes = (
                "Mocked until DATAFORSEO_LOGIN/PASSWORD (preferred) or GOOGLE_ADS_* "
                "are set and GUM_FORCE_MOCK_PROVIDERS=false."
            )
        return ProviderStatus(
            name=self.name,
            mode=mode,
            configured=configured,
            capabilities=self.capabilities,
            notes=notes,
        )

    def search(self, request: ProviderRequest) -> ProviderResponse:
        if self._live_via_dataforseo():
            return self._live_dataforseo_keyword_overview(request)
        return self._mock_search(request)

    def _mock_search(self, request: ProviderRequest) -> ProviderResponse:
        items = [
            ProviderResultItem(
                title=f"[MOCK google_ads] keyword idea: {request.query}",
                snippet="Placeholder Keyword Planner idea — UNVERIFIED_CLAIM.",
                claim_tag=ClaimTag.UNVERIFIED_CLAIM,
                attributes={
                    "avg_monthly_searches": None,
                    "competition": None,
                    "mocked": True,
                },
            ),
            ProviderResultItem(
                title=f"[MOCK google_ads] related: best {request.query} tools",
                snippet="Synthetic related keyword — not from Keyword Planner.",
                claim_tag=ClaimTag.UNVERIFIED_CLAIM,
                attributes={"avg_monthly_searches": None, "mocked": True},
            ),
        ]
        return mock_response(
            provider=self.name,
            request=request,
            summary=f"Mocked Google Ads keyword ideas for '{request.query}'",
            items=items[: request.limit],
            limitations=[
                "Keyword adapter returned MOCK data — volumes are not measured.",
                "No Google Ads or DataForSEO keyword API call was made.",
                "Volumes/competition fields are intentionally null while mocked.",
            ],
            raw={"adapter": "google_ads", "mocked": True},
        )

    def _live_dataforseo_keyword_overview(
        self, request: ProviderRequest
    ) -> ProviderResponse:
        login = (self.settings.dataforseo_login or "").strip()
        password = (self.settings.dataforseo_password or "").strip()
        if not login or not password:
            return self._mock_search(request)

        base = (
            self.settings.dataforseo_base_url or DEFAULT_DATAFORSEO_BASE_URL
        ).strip()
        task = {
            "keywords": [request.query],
            "location_code": resolve_location_code(request.geography),
            "language_code": resolve_language_code(request.language),
            "include_serp_info": False,
            "include_clickstream_data": False,
        }

        owns_client = self._http_client is None
        client = self._http_client or httpx.Client(timeout=60.0)
        try:
            try:
                response = dataforseo_post(
                    client=client,
                    base_url=base,
                    login=login,
                    password=password,
                    path="/v3/dataforseo_labs/google/keyword_overview/live",
                    payload=[task],
                )
            except httpx.RequestError as exc:
                return unavailable_response(
                    provider=self.name,
                    request=request,
                    reason="network_error",
                    detail=(
                        "DataForSEO keyword overview failed before a response: "
                        f"{exc.__class__.__name__}"
                    ),
                    http_status=None,
                )
        finally:
            if owns_client:
                client.close()

        payload = safe_json(response)
        failure = classify_dataforseo_failure(
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
                raw_body={
                    "status_code": payload.get("status_code"),
                    "status_message": payload.get("status_message"),
                },
            )

        items: list[ProviderResultItem] = []
        for row in _extract_keyword_rows(payload)[: request.limit]:
            keyword = row.get("keyword") or request.query
            info = row.get("keyword_info") or {}
            volume = info.get("search_volume")
            competition = info.get("competition")
            competition_level = info.get("competition_level")
            cpc = info.get("cpc")
            items.append(
                ProviderResultItem(
                    title=f"Keyword overview: {keyword}",
                    snippet=(
                        f"DataForSEO keyword overview for '{keyword}' "
                        f"(search_volume={volume}, competition={competition_level})."
                    ),
                    claim_tag=ClaimTag.MEASURED_FACT,
                    attributes={
                        "source": "dataforseo_keyword_overview",
                        "backend": "dataforseo",
                        "keyword": keyword,
                        "avg_monthly_searches": volume,
                        "competition": competition,
                        "competition_level": competition_level,
                        "cpc": cpc,
                        "monthly_searches": info.get("monthly_searches"),
                        "mocked": False,
                        "claim_note": (
                            "MEASURED_FACT = payload observed from DataForSEO; "
                            "search_volume/competition are provider estimates "
                            "(Google Ads–derived), not purchase-intent proof."
                        ),
                    },
                    score=float(volume) if isinstance(volume, (int, float)) else None,
                )
            )

        return ProviderResponse(
            provider=self.name,
            mode=ProviderMode.LIVE,
            query=request.query,
            summary=(
                f"Live DataForSEO keyword overview for '{request.query}': "
                f"{len(items)} keyword row(s)."
            ),
            claim_tag=ClaimTag.MEASURED_FACT,
            fetched_at=utcnow(),
            cached=False,
            items=items,
            limitations=[
                "Live keyword metrics via DataForSEO Labs Keyword Overview.",
                "Search volume / competition are provider estimates, not measured sales.",
                "Do not treat volumes as purchase-intent or total addressable market.",
            ],
            raw={
                "adapter": "google_ads",
                "backend": "dataforseo",
                "mocked": False,
                "mode": ProviderMode.LIVE.value,
                "http_status": response.status_code,
                "dfs_status_code": payload.get("status_code"),
                "returned_items": len(items),
                "cost": payload.get("cost"),
            },
        )


def _extract_keyword_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for task in payload.get("tasks") or []:
        for result in task.get("result") or []:
            items = result.get("items")
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, dict):
                        rows.append(item)
            elif isinstance(result, dict) and result.get("keyword"):
                rows.append(result)
    return rows
