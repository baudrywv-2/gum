"""Provider credential / feature flags (env-driven; no secrets required for M2)."""

from __future__ import annotations

from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from providers.serpapi_http import DEFAULT_SERPAPI_BASE_URL


class ProviderSettings(BaseSettings):
    """Credentials are optional. Without them, adapters run in explicit MOCK mode."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    force_mock_providers: bool = Field(default=True, alias="GUM_FORCE_MOCK_PROVIDERS")
    cache_ttl_seconds: int = Field(default=300, alias="GUM_PROVIDER_CACHE_TTL_SECONDS")
    cache_enabled: bool = Field(default=True, alias="GUM_PROVIDER_CACHE_ENABLED")

    # Google Ads / Keyword Planner
    google_ads_developer_token: str | None = Field(
        default=None, alias="GOOGLE_ADS_DEVELOPER_TOKEN"
    )
    google_ads_client_id: str | None = Field(default=None, alias="GOOGLE_ADS_CLIENT_ID")
    google_ads_client_secret: str | None = Field(
        default=None, alias="GOOGLE_ADS_CLIENT_SECRET"
    )
    google_ads_refresh_token: str | None = Field(
        default=None, alias="GOOGLE_ADS_REFRESH_TOKEN"
    )
    google_ads_customer_id: str | None = Field(
        default=None, alias="GOOGLE_ADS_CUSTOMER_ID"
    )

    # Google Trends flag (informational; live Trends uses SERPAPI_API_KEY)
    google_trends_enabled: bool = Field(default=False, alias="GOOGLE_TRENDS_ENABLED")

    # SerpAPI — organic Google SERP + Google Trends (same key)
    serp_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("SERPAPI_API_KEY", "SERP_API_KEY"),
        serialization_alias="SERPAPI_API_KEY",
    )
    serp_api_base_url: str = Field(
        default=DEFAULT_SERPAPI_BASE_URL,
        validation_alias=AliasChoices("SERP_API_BASE_URL", "SERPAPI_BASE_URL"),
        serialization_alias="SERP_API_BASE_URL",
    )

    # X API
    x_api_bearer_token: str | None = Field(default=None, alias="X_API_BEARER_TOKEN")
    x_api_base_url: str = Field(
        default="https://api.x.com/2", alias="X_API_BASE_URL"
    )

    def google_ads_configured(self) -> bool:
        return all(
            [
                self.google_ads_developer_token,
                self.google_ads_client_id,
                self.google_ads_client_secret,
                self.google_ads_refresh_token,
                self.google_ads_customer_id,
            ]
        )

    def serp_configured(self) -> bool:
        return bool(self.serp_api_key)

    def x_api_configured(self) -> bool:
        return bool(self.x_api_bearer_token)

    def should_mock(self, configured: bool) -> bool:
        if self.force_mock_providers:
            return True
        return not configured


@lru_cache
def get_provider_settings() -> ProviderSettings:
    return ProviderSettings()


def reset_provider_settings() -> None:
    get_provider_settings.cache_clear()
