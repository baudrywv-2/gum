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
                "market size. No live X API calls while mocked."
            ),
        )

    def search(self, request: ProviderRequest) -> ProviderResponse:
        items = [
            ProviderResultItem(
                title=f"[MOCK x_api] Frustrated with {request.query}",
                snippet=(
                    f"I hate how hard it is to find a good solution for {request.query}. "
                    "Wish there was something simpler that doesn't waste my time."
                ),
                url="https://x.com/example/status/0",
                claim_tag=ClaimTag.UNVERIFIED_CLAIM,
                attributes={
                    "author": "@mock_user",
                    "engagement": {"likes": 0, "reposts": 0},
                    "mocked": True,
                },
            ),
            ProviderResultItem(
                title=f"[MOCK x_api] InvoiceBot issue with {request.query}",
                snippet=(
                    f"Problem with InvoiceBot for {request.query}: too expensive "
                    "and it fails to cover basic exports. Missing a simple CSV feature."
                ),
                url="https://x.com/example/status/1",
                claim_tag=ClaimTag.UNVERIFIED_CLAIM,
                attributes={
                    "author": "@mock_user_2",
                    "engagement": {"likes": 0, "reposts": 0},
                    "mocked": True,
                    "mentioned_competitor": "InvoiceBot",
                },
            ),
        ]
        return mock_response(
            provider=self.name,
            request=request,
            summary=f"Mocked X recent-search for '{request.query}'",
            items=items[: request.limit],
            limitations=[
                "X API adapter is a stub — posts are synthetic placeholders.",
                "No live X API request was made.",
                "Social signals are not purchase-intent proof.",
            ],
            raw={"adapter": "x_api", "mocked": True},
        )
