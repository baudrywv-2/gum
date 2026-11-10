"""Provider interface and shared helpers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone

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


class Provider(ABC):
    """Replaceable data-source adapter.

    Adapters must never invent measured demand. Mock/stub responses are tagged
    UNVERIFIED_CLAIM (or HYPOTHESIS) and declare mode=MOCK until credentials exist.
    """

    name: ProviderName
    capabilities: list[ProviderCapability]

    @abstractmethod
    def status(self) -> ProviderStatus:
        raise NotImplementedError

    @abstractmethod
    def search(self, request: ProviderRequest) -> ProviderResponse:
        raise NotImplementedError

    def is_configured(self) -> bool:
        return self.status().configured

    def operating_mode(self) -> ProviderMode:
        return self.status().mode


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def mock_response(
    *,
    provider: ProviderName,
    request: ProviderRequest,
    summary: str,
    items: list[ProviderResultItem] | None = None,
    limitations: list[str] | None = None,
    raw: dict | None = None,
) -> ProviderResponse:
    return ProviderResponse(
        provider=provider,
        mode=ProviderMode.MOCK,
        query=request.query,
        summary=summary,
        claim_tag=ClaimTag.UNVERIFIED_CLAIM,
        fetched_at=utcnow(),
        cached=False,
        items=items or [],
        limitations=limitations
        or [
            "Mocked response — no live provider credentials configured.",
            "Do not treat results as measured demand.",
        ],
        raw=raw or {"mocked": True, "provider": provider.value},
    )
