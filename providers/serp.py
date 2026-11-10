"""SERP provider adapter — live Google organic via SerpAPI when configured; else mock."""

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


class SerpProvider(Provider):
    name = ProviderName.SERP
    capabilities = [ProviderCapability.SERP_SNAPSHOT]

    def __init__(
        self,
        settings: ProviderSettings | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.settings = settings or get_provider_settings()
        self._http_client = http_client

    def _should_mock(self) -> bool:
        return self.settings.should_mock(self.settings.serp_configured())

    def status(self) -> ProviderStatus:
        configured = self.settings.serp_configured()
        if self._should_mock():
            mode = ProviderMode.MOCK
            notes = (
                "SerpAPI backend (SERP_PROVIDER=serpapi). Mocked until SERPAPI_API_KEY "
                "is set and GUM_FORCE_MOCK_PROVIDERS=false. Set SERP_PROVIDER=dataforseo "
                "to use DataForSEO instead. SERP snapshots are not demand proof."
            )
        else:
            mode = ProviderMode.LIVE
            notes = (
                "Live Google organic SERP via SerpAPI (primary backend). Rankings are a "
                "point-in-time snapshot — not purchase-intent or market-size proof."
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
        slug = request.query.strip().lower().replace(" ", "-") or "topic"
        items = [
            ProviderResultItem(
                title=f"InvoiceBot — {request.query} software",
                snippet=f"Mocked SERP listing for InvoiceBot covering {request.query}.",
                url=f"https://invoicebot.example.invalid/{slug}",
                claim_tag=ClaimTag.UNVERIFIED_CLAIM,
                attributes={"position": 1, "mocked": True, "brand": "InvoiceBot"},
            ),
            ProviderResultItem(
                title=f"Ledgerly Guide: {request.query}",
                snippet=f"Mocked guide page from Ledgerly about {request.query}.",
                url=f"https://ledgerly.example.invalid/guides/{slug}",
                claim_tag=ClaimTag.UNVERIFIED_CLAIM,
                attributes={"position": 2, "mocked": True, "brand": "Ledgerly"},
            ),
            ProviderResultItem(
                title=f"PayStacker — best {request.query} tools",
                snippet="Mocked comparison-style SERP hit (synthetic).",
                url=f"https://paystacker.example.invalid/tools/{slug}",
                claim_tag=ClaimTag.UNVERIFIED_CLAIM,
                attributes={"position": 3, "mocked": True, "brand": "PayStacker"},
            ),
        ]
        return mock_response(
            provider=self.name,
            request=request,
            summary=f"Mocked SERP snapshot for '{request.query}'",
            items=items[: request.limit],
            limitations=[
                "SERP adapter returned MOCK data — listings are synthetic placeholders.",
                "No external SerpAPI call was made.",
                "SERP rankings are not purchase-intent proof.",
            ],
            raw={"adapter": "serp", "mocked": True},
        )

    def _live_search(self, request: ProviderRequest) -> ProviderResponse:
        api_key = (self.settings.serp_api_key or "").strip()
        if not api_key:
            return self._mock_search(request)

        base = (self.settings.serp_api_base_url or DEFAULT_SERPAPI_BASE_URL).strip()
        params: dict[str, Any] = {
            "engine": "google",
            "q": request.query,
            "num": max(1, min(100, request.limit)),
        }
        if request.geography:
            params["gl"] = request.geography.strip().lower()
        if request.language:
            params["hl"] = request.language.strip().lower()

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
                        f"SerpAPI request failed before a response: "
                        f"{exc.__class__.__name__}"
                    ),
                    http_status=None,
                )
        finally:
            if owns_client:
                client.close()

        payload = safe_json(response)
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
                raw_body={"error": payload.get("error")} if payload.get("error") else {},
            )

        organic = payload.get("organic_results") or []
        items: list[ProviderResultItem] = []
        for row in organic[: request.limit]:
            position = row.get("position")
            title = (row.get("title") or "").strip() or f"SERP result {position}"
            link = row.get("link") or row.get("url")
            snippet = row.get("snippet")
            items.append(
                ProviderResultItem(
                    title=title,
                    snippet=snippet,
                    url=link,
                    claim_tag=ClaimTag.MEASURED_FACT,
                    attributes={
                        "source": "serpapi_google_organic",
                        "position": position,
                        "displayed_link": row.get("displayed_link"),
                        "mocked": False,
                        "claim_note": (
                            "MEASURED_FACT = organic result observed in this SerpAPI "
                            "Google snapshot; not proof of demand volume."
                        ),
                    },
                )
            )

        return ProviderResponse(
            provider=self.name,
            mode=ProviderMode.LIVE,
            query=request.query,
            summary=(
                f"Live SerpAPI Google organic for '{request.query}': "
                f"{len(items)} result(s)."
            ),
            claim_tag=ClaimTag.MEASURED_FACT,
            fetched_at=utcnow(),
            cached=False,
            items=items,
            limitations=[
                "Live Google SERP snapshot via SerpAPI — point-in-time rankings only.",
                "Organic result counts are not search-volume or purchase-intent proof.",
                "Do not invent demand from SERP presence alone.",
            ],
            raw={
                "adapter": "serp",
                "mocked": False,
                "mode": ProviderMode.LIVE.value,
                "http_status": response.status_code,
                "engine": "google",
                "organic_count": len(organic),
                "returned_items": len(items),
                "search_metadata": payload.get("search_metadata") or {},
            },
        )
