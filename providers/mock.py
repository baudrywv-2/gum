"""Always-on mock provider for tests and local development."""

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


class MockProvider(Provider):
    name = ProviderName.MOCK
    capabilities = [
        ProviderCapability.GENERIC_SEARCH,
        ProviderCapability.KEYWORD_IDEAS,
        ProviderCapability.TREND_INTEREST,
        ProviderCapability.SERP_SNAPSHOT,
        ProviderCapability.SOCIAL_SEARCH,
    ]

    def status(self) -> ProviderStatus:
        return ProviderStatus(
            name=self.name,
            mode=ProviderMode.MOCK,
            configured=True,
            capabilities=self.capabilities,
            notes="Deterministic mock provider for tests and local development.",
        )

    def search(self, request: ProviderRequest) -> ProviderResponse:
        items = [
            ProviderResultItem(
                title=f"Mock insight for '{request.query}'",
                snippet="Synthetic placeholder — not measured demand.",
                claim_tag=ClaimTag.UNVERIFIED_CLAIM,
                attributes={"rank": 1, "source": "mock"},
            ),
            ProviderResultItem(
                title=f"Related mock signal: {request.query} alternatives",
                snippet=(
                    f"Users struggle with {request.query}; annoying gaps remain and "
                    "people wish there was a clearer option."
                ),
                claim_tag=ClaimTag.HYPOTHESIS,
                attributes={"rank": 2, "source": "mock"},
            ),
        ]
        return mock_response(
            provider=self.name,
            request=request,
            summary=f"Mock result for query: {request.query}",
            items=items[: request.limit],
            raw={"source": "mock", "query": request.query},
        )
