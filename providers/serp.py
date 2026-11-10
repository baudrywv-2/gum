"""SERP provider adapter — MOCK until SERP_API_KEY is configured (still stubbed)."""

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
                "Stubbed/mocked. Set SERP_API_KEY and disable force-mock for future live SERP. "
                "No paid SERP requests are issued while mocked."
            ),
        )

    def search(self, request: ProviderRequest) -> ProviderResponse:
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
                "SERP adapter is a stub — listings are synthetic placeholders.",
                "No external SERP API call was made.",
            ],
            raw={"adapter": "serp", "mocked": True},
        )
