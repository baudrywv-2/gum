"""SERP provider adapter — MOCK until SERP_API_KEY is configured (still stubbed in M2)."""

from __future__ import annotations

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
from providers.base import Provider, mock_response
from providers.config import ProviderSettings, get_provider_settings


class SerpProvider(Provider):
    name = ProviderName.SERP
    capabilities = [ProviderCapability.SERP_SNAPSHOT]

    def __init__(self, settings: ProviderSettings | None = None) -> None:
        self.settings = settings or get_provider_settings()

    def status(self) -> ProviderStatus:
        configured = self.settings.serp_configured()
        return ProviderStatus(
            name=self.name,
            mode=ProviderMode.MOCK,
            configured=configured,
            capabilities=self.capabilities,
            notes=(
                "Stubbed/mocked. Set SERP_API_KEY and disable force-mock for future live SERP."
                " Milestone 2 never issues paid SERP requests."
            ),
        )

    def search(self, request: ProviderRequest) -> ProviderResponse:
        items = [
            ProviderResultItem(
                title=f"[MOCK serp] Result about {request.query}",
                snippet="Synthetic organic result for adapter testing.",
                url=f"https://example.invalid/search?q={request.query.replace(' ', '+')}",
                claim_tag=ClaimTag.UNVERIFIED_CLAIM,
                attributes={"position": 1, "mocked": True},
            ),
            ProviderResultItem(
                title=f"[MOCK serp] Guide: {request.query}",
                snippet="Second synthetic SERP hit — not a real crawl.",
                url="https://example.invalid/guide",
                claim_tag=ClaimTag.UNVERIFIED_CLAIM,
                attributes={"position": 2, "mocked": True},
            ),
        ]
        return mock_response(
            provider=self.name,
            request=request,
            summary=f"Mocked SERP snapshot for '{request.query}'",
            items=items[: request.limit],
            limitations=[
                "SERP adapter is a stub in Milestone 2.",
                "No external SERP API call was made.",
            ],
            raw={"adapter": "serp", "mocked": True},
        )
