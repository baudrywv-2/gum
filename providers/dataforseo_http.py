"""Shared DataForSEO HTTP helpers (Basic auth; never log credentials)."""

from __future__ import annotations

import base64
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

DEFAULT_DATAFORSEO_BASE_URL = "https://api.dataforseo.com"

# Common geography shorthand → DataForSEO location_code
LOCATION_CODES: dict[str, int] = {
    "us": 2840,
    "usa": 2840,
    "united states": 2840,
    "uk": 2826,
    "gb": 2826,
    "united kingdom": 2826,
    "ca": 2124,
    "canada": 2124,
    "au": 2036,
    "australia": 2036,
}


def resolve_location_code(geography: str | None) -> int:
    if not geography:
        return 2840
    key = geography.strip().lower()
    if key.isdigit():
        return int(key)
    return LOCATION_CODES.get(key, 2840)


def resolve_language_code(language: str | None) -> str:
    if not language:
        return "en"
    return language.strip().lower()[:2] or "en"


def basic_auth_header(login: str, password: str) -> str:
    token = base64.b64encode(f"{login}:{password}".encode("utf-8")).decode("ascii")
    return f"Basic {token}"


def safe_json(response: httpx.Response) -> dict[str, Any]:
    try:
        data = response.json()
    except ValueError:
        return {"non_json_body": True}
    return data if isinstance(data, dict) else {"value": data}


def classify_dataforseo_failure(
    *,
    http_status: int | None,
    payload: dict[str, Any] | None,
) -> tuple[str, str] | None:
    """Return (reason, detail) when the call should be treated as unavailable."""
    payload = payload or {}
    if http_status in (401, 403):
        return (
            "auth_error",
            f"DataForSEO authentication/authorization failed (HTTP {http_status}). "
            "No results fabricated.",
        )
    if http_status == 429:
        return (
            "rate_limited",
            "DataForSEO rate limit reached (HTTP 429). No synthetic volume returned.",
        )
    if http_status is not None and http_status >= 400:
        return (
            "http_error",
            f"DataForSEO returned HTTP {http_status}. No results fabricated.",
        )

    status_code = payload.get("status_code")
    status_message = str(payload.get("status_message") or "").strip()
    lowered = status_message.lower()

    if status_code in (None, 20000):
        # Inspect tasks for nested failures.
        tasks = payload.get("tasks") or []
        for task in tasks:
            task_code = task.get("status_code")
            task_msg = str(task.get("status_message") or "")
            if task_code not in (None, 20000):
                return _classify_status(task_code, task_msg)
        return None

    return _classify_status(status_code, status_message or lowered)


def _classify_status(status_code: Any, message: str) -> tuple[str, str]:
    lowered = (message or "").lower()
    code = int(status_code) if str(status_code).isdigit() else None
    auth_codes = {40100, 40101, 40102, 40103, 40104, 40105}
    balance_codes = {40200, 40201, 40202, 40203, 40204, 40205, 40206}
    if code in auth_codes or any(
        m in lowered for m in ("unauthor", "forbidden", "login", "password", "auth")
    ):
        return (
            "auth_error",
            f"DataForSEO auth error (code={status_code}): {message or 'unauthorized'}. "
            "No results fabricated.",
        )
    if code in balance_codes or any(
        m in lowered
        for m in ("balance", "payment", "credit", "fund", "money", "not enough")
    ):
        return (
            "balance_error",
            f"DataForSEO balance/payment error (code={status_code}): "
            f"{message or 'insufficient balance'}. No synthetic volume returned.",
        )
    return (
        "provider_error",
        f"DataForSEO error (code={status_code}): {message or 'unknown'}. "
        "No results fabricated.",
    )


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
            "backend": "dataforseo",
            "mocked": False,
            "mode": ProviderMode.UNAVAILABLE.value,
            "error": reason,
            "http_status": http_status,
            "body": raw_body or {},
        },
    )


def dataforseo_post(
    *,
    client: httpx.Client,
    base_url: str,
    login: str,
    password: str,
    path: str,
    payload: list[dict[str, Any]],
) -> httpx.Response:
    root = base_url.rstrip("/")
    url = f"{root}{path if path.startswith('/') else '/' + path}"
    headers = {
        "Authorization": basic_auth_header(login, password),
        "Content-Type": "application/json",
    }
    return client.post(url, headers=headers, json=payload)
