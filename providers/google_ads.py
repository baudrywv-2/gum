"""Google Ads / Keyword Planner adapter — MOCK until credentials are configured."""

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


class GoogleAdsProvider(Provider):
    name = ProviderName.GOOGLE_ADS
    capabilities = [ProviderCapability.KEYWORD_IDEAS]

    def __init__(self, settings: ProviderSettings | None = None) -> None:
        self.settings = settings or get_provider_settings()

    def status(self) -> ProviderStatus:
        configured = self.settings.google_ads_configured()
        mocked = self.settings.should_mock(configured)
        if mocked:
            mode = ProviderMode.MOCK
            notes = (
                "Stubbed/mocked. Set GOOGLE_ADS_* credentials and "
                "GUM_FORCE_MOCK_PROVIDERS=false to enable live Keyword Planner calls."
            )
        else:
            mode = ProviderMode.LIVE
            notes = "Credentials present — live client not yet implemented in M2."
            # M2 deliberately does not call paid/live APIs even if creds exist.
            mode = ProviderMode.MOCK
            notes = (
                "Credentials detected but M2 ships stub only — no live Google Ads calls."
            )
        return ProviderStatus(
            name=self.name,
            mode=mode,
            configured=configured,
            capabilities=self.capabilities,
            notes=notes,
        )

    def search(self, request: ProviderRequest) -> ProviderResponse:
        items = [
            ProviderResultItem(
                title=f"[MOCK google_ads] keyword idea: {request.query}",
                snippet="Placeholder Keyword Planner idea — UNVERIFIED_CLAIM.",
                claim_tag=ClaimTag.UNVERIFIED_CLAIM,
                attributes={
                    "avg_monthly_searches": None,
                    "competition": None,
                    "mocked": True,
                },
            ),
            ProviderResultItem(
                title=f"[MOCK google_ads] related: best {request.query} tools",
                snippet="Synthetic related keyword — not from Keyword Planner.",
                claim_tag=ClaimTag.UNVERIFIED_CLAIM,
                attributes={"avg_monthly_searches": None, "mocked": True},
            ),
        ]
        return mock_response(
            provider=self.name,
            request=request,
            summary=f"Mocked Google Ads keyword ideas for '{request.query}'",
            items=items[: request.limit],
            limitations=[
                "Google Ads adapter is a stub in Milestone 2.",
                "No Keyword Planner API call was made.",
                "Volumes/competition fields are intentionally null.",
            ],
            raw={"adapter": "google_ads", "mocked": True},
        )
