"""X (Twitter) API adapter — MOCK until X_API_BEARER_TOKEN is configured."""

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


class XApiProvider(Provider):
    name = ProviderName.X_API
    capabilities = [ProviderCapability.SOCIAL_SEARCH]

    def __init__(self, settings: ProviderSettings | None = None) -> None:
        self.settings = settings or get_provider_settings()

    def status(self) -> ProviderStatus:
        configured = self.settings.x_api_configured()
        return ProviderStatus(
            name=self.name,
            mode=ProviderMode.MOCK,
            configured=configured,
            capabilities=self.capabilities,
            notes=(
                "Stubbed/mocked. X posts are discovery signals only — never proof of "
                "market size. Milestone 2 does not call the live X API."
            ),
        )

    def search(self, request: ProviderRequest) -> ProviderResponse:
        items = [
            ProviderResultItem(
                title=f"[MOCK x_api] Recent post mentioning {request.query}",
                snippet="Synthetic social signal for pipeline tests.",
                url="https://x.com/example/status/0",
                claim_tag=ClaimTag.UNVERIFIED_CLAIM,
                attributes={
                    "author": "@mock_user",
                    "engagement": {"likes": 0, "reposts": 0},
                    "mocked": True,
                },
            )
        ]
        return mock_response(
            provider=self.name,
            request=request,
            summary=f"Mocked X recent-search for '{request.query}'",
            items=items[: request.limit],
            limitations=[
                "X API adapter is a stub in Milestone 2.",
                "No live X API request was made.",
                "Social signals are not purchase-intent proof.",
            ],
            raw={"adapter": "x_api", "mocked": True},
        )
