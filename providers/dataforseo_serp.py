"""DataForSEO Google organic SERP adapter (alternate SERP backend)."""

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


class DataForSeoSerpProvider(Provider):
    """Live organic SERP via DataForSEO; mock when credentials missing / force-mock."""

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
        return self.settings.should_mock(self.settings.dataforseo_configured())

    def status(self) -> ProviderStatus:
        configured = self.settings.dataforseo_configured()
        if self._should_mock():
            mode = ProviderMode.MOCK
            notes = (
                "Mocked until DATAFORSEO_LOGIN/PASSWORD are set and "
                "GUM_FORCE_MOCK_PROVIDERS=false (SERP_PROVIDER=dataforseo). "
                "SERP snapshots are discovery signals only — not demand proof."
            )
        else:
            mode = ProviderMode.LIVE
            notes = (
                "Live Google organic SERP via DataForSEO. Rankings are a "
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
                attributes={
                    "position": 1,
                    "mocked": True,
                    "brand": "InvoiceBot",
                    "backend": "dataforseo",
                },
            ),
            ProviderResultItem(
                title=f"Ledgerly Guide: {request.query}",
                snippet=f"Mocked guide page from Ledgerly about {request.query}.",
                url=f"https://ledgerly.example.invalid/guides/{slug}",
                claim_tag=ClaimTag.UNVERIFIED_CLAIM,
                attributes={
                    "position": 2,
                    "mocked": True,
                    "brand": "Ledgerly",
                    "backend": "dataforseo",
                },
            ),
        ]
        return mock_response(
            provider=self.name,
            request=request,
            summary=f"Mocked DataForSEO SERP snapshot for '{request.query}'",
            items=items[: request.limit],
            limitations=[
                "DataForSEO SERP adapter returned MOCK data — synthetic placeholders.",
                "No DataForSEO API call was made.",
                "SERP rankings are not purchase-intent proof.",
            ],
            raw={"adapter": "serp", "backend": "dataforseo", "mocked": True},
        )

    def _live_search(self, request: ProviderRequest) -> ProviderResponse:
        login = (self.settings.dataforseo_login or "").strip()
        password = (self.settings.dataforseo_password or "").strip()
        if not login or not password:
            return self._mock_search(request)

        base = (
            self.settings.dataforseo_base_url or DEFAULT_DATAFORSEO_BASE_URL
        ).strip()
        # Keep depth <= 10 for a single cheap SERP unit when possible.
        depth = max(10, min(100, request.limit if request.limit >= 10 else 10))
        task = {
            "keyword": request.query,
            "location_code": resolve_location_code(request.geography),
            "language_code": resolve_language_code(request.language),
            "depth": depth,
            "device": "desktop",
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
                    path="/v3/serp/google/organic/live/regular",
                    payload=[task],
                )
            except httpx.RequestError as exc:
                return unavailable_response(
                    provider=self.name,
                    request=request,
                    reason="network_error",
                    detail=(
                        "DataForSEO SERP request failed before a response: "
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

        organic_rows = _extract_organic_items(payload)
        items: list[ProviderResultItem] = []
        for row in organic_rows[: request.limit]:
            if str(row.get("type") or "organic") not in ("organic", "featured_snippet"):
                # Regular endpoint mainly returns organic/paid; keep organic-like rows.
                if row.get("type") == "paid":
                    continue
            title = (row.get("title") or "").strip() or "SERP result"
            url = row.get("url") or row.get("link")
            snippet = row.get("description") or row.get("snippet")
            position = row.get("rank_group") or row.get("rank_absolute")
            items.append(
                ProviderResultItem(
                    title=title,
                    snippet=snippet,
                    url=url,
                    claim_tag=ClaimTag.MEASURED_FACT,
                    attributes={
                        "source": "dataforseo_google_organic",
                        "backend": "dataforseo",
                        "position": position,
                        "rank_absolute": row.get("rank_absolute"),
                        "domain": row.get("domain"),
                        "mocked": False,
                        "claim_note": (
                            "MEASURED_FACT = organic result observed in this "
                            "DataForSEO SERP snapshot; not proof of demand volume."
                        ),
                    },
                )
            )

        return ProviderResponse(
            provider=self.name,
            mode=ProviderMode.LIVE,
            query=request.query,
            summary=(
                f"Live DataForSEO Google organic for '{request.query}': "
                f"{len(items)} result(s)."
            ),
            claim_tag=ClaimTag.MEASURED_FACT,
            fetched_at=utcnow(),
            cached=False,
            items=items,
            limitations=[
                "Live Google SERP snapshot via DataForSEO — point-in-time rankings only.",
                "Organic result counts are not search-volume or purchase-intent proof.",
                "Do not invent demand from SERP presence alone.",
            ],
            raw={
                "adapter": "serp",
                "backend": "dataforseo",
                "mocked": False,
                "mode": ProviderMode.LIVE.value,
                "http_status": response.status_code,
                "dfs_status_code": payload.get("status_code"),
                "organic_count": len(organic_rows),
                "returned_items": len(items),
                "cost": payload.get("cost"),
            },
        )


def _extract_organic_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for task in payload.get("tasks") or []:
        for result in task.get("result") or []:
            for item in result.get("items") or []:
                if not isinstance(item, dict):
                    continue
                item_type = str(item.get("type") or "organic")
                if item_type in ("organic", "featured_snippet"):
                    rows.append(item)
    return rows
