"""Google Trends adapter — MOCK stub (no live client in Milestone 2)."""

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


class GoogleTrendsProvider(Provider):
    name = ProviderName.GOOGLE_TRENDS
    capabilities = [ProviderCapability.TREND_INTEREST]

    def __init__(self, settings: ProviderSettings | None = None) -> None:
        self.settings = settings or get_provider_settings()

    def status(self) -> ProviderStatus:
        configured = bool(self.settings.google_trends_enabled)
        return ProviderStatus(
            name=self.name,
            mode=ProviderMode.MOCK,
            configured=configured,
            capabilities=self.capabilities,
            notes=(
                "Stubbed/mocked. Interest-over-time values are synthetic placeholders."
            ),
        )

    def search(self, request: ProviderRequest) -> ProviderResponse:
        items = [
            ProviderResultItem(
                title=f"[MOCK google_trends] interest: {request.query}",
                snippet="Synthetic interest series — not measured Trends data.",
                claim_tag=ClaimTag.UNVERIFIED_CLAIM,
                attributes={
                    "interest_over_time": [12, 18, 15, 22, 19],
                    "mocked": True,
                },
            )
        ]
        return mock_response(
            provider=self.name,
            request=request,
            summary=f"Mocked Google Trends interest for '{request.query}'",
            items=items[: request.limit],
            limitations=[
                "Google Trends adapter is a stub in Milestone 2.",
                "Interest values are fabricated for pipeline testing only.",
            ],
            raw={"adapter": "google_trends", "mocked": True},
        )
