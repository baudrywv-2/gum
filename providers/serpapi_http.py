"""Shared SerpAPI HTTP helpers (no secrets logged)."""

from __future__ import annotations

from typing import Any

import httpx

from packages.contracts.claim_tags import ClaimTag
from packages.contracts.providers import (
    ProviderMode,
    ProviderName,
    ProviderRequest,
    ProviderResponse,
)
from providers.base import utcnow

DEFAULT_SERPAPI_BASE_URL = "https://serpapi.com"


def safe_json(response: httpx.Response) -> dict[str, Any]:
    try:
        data = response.json()
    except ValueError:
        return {"non_json_body": True}
    return data if isinstance(data, dict) else {"value": data}


def classify_serpapi_failure(
    *,
    http_status: int | None,
    payload: dict[str, Any] | None,
) -> tuple[str, str] | None:
    """Return (reason, detail) when the call should be treated as unavailable."""
    payload = payload or {}
    error_text = str(payload.get("error") or "").strip()
    lowered = error_text.lower()

    if http_status in (401, 403):
        return (
            "auth_error",
            f"SerpAPI authentication/authorization failed (HTTP {http_status}). "
            "No results fabricated.",
        )
    if http_status == 429:
        return (
            "rate_limited",
            "SerpAPI rate limit reached (HTTP 429). No synthetic volume returned.",
        )
    if http_status is not None and http_status >= 400:
        return (
            "http_error",
            f"SerpAPI returned HTTP {http_status}. No results fabricated.",
        )

    if error_text:
        quota_markers = (
            "run out",
            "ran out",
            "quota",
            "credit",
            "limit",
            "exceed",
            "payment",
            "subscription",
        )
        auth_markers = ("invalid api key", "unauthorized", "forbidden", "api_key")
        if any(m in lowered for m in quota_markers):
            return (
                "quota_error",
                f"SerpAPI quota/credits error: {error_text}. No synthetic volume returned.",
            )
        if any(m in lowered for m in auth_markers):
            return (
                "auth_error",
                f"SerpAPI auth error: {error_text}. No results fabricated.",
            )
        return (
            "provider_error",
            f"SerpAPI error: {error_text}. No results fabricated.",
        )
    return None


def unavailable_response(
    *,
    provider: ProviderName,
    request: ProviderRequest,
    reason: str,
    detail: str,
    http_status: int | None,
    raw_body: dict[str, Any] | None = None,
) -> ProviderResponse:
    return ProviderResponse(
        provider=provider,
        mode=ProviderMode.UNAVAILABLE,
        query=request.query,
        summary=f"{provider.value} unavailable ({reason}): {detail}",
        claim_tag=ClaimTag.UNVERIFIED_CLAIM,
        fetched_at=utcnow(),
        cached=False,
        items=[],
        limitations=[
            detail,
            "No mock/synthetic results substituted for this failure.",
            "Do not treat absence of results here as measured zero demand.",
        ],
        raw={
            "adapter": provider.value,
            "mocked": False,
            "mode": ProviderMode.UNAVAILABLE.value,
            "error": reason,
            "http_status": http_status,
            "body": raw_body or {},
        },
    )


def serpapi_get(
    *,
    client: httpx.Client,
    base_url: str,
    api_key: str,
    params: dict[str, Any],
) -> httpx.Response:
    root = base_url.rstrip("/")
    # Accept either https://serpapi.com or https://serpapi.com/search(.json)
    if root.endswith("/search.json") or root.endswith("/search"):
        url = root
    else:
        url = f"{root}/search.json"
    query = {**params, "api_key": api_key}
    return client.get(url, params=query)
