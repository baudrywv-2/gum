"""Provider registry + cached/search facade with usage tracking."""

from __future__ import annotations

from functools import lru_cache

from packages.contracts.providers import (
    ProviderName,
    ProviderRequest,
    ProviderResponse,
    ProviderStatus,
)
from providers.base import Provider
from providers.cache import ProviderCache
from providers.config import ProviderSettings, get_provider_settings
from providers.google_ads import GoogleAdsProvider
from providers.google_trends import GoogleTrendsProvider
from providers.mock import MockProvider
from providers.serp import SerpProvider
from providers.usage import UsageTracker
from providers.x_api import XApiProvider
from providers.youtube import YouTubeProvider


class ProviderRegistry:
    def __init__(
        self,
        settings: ProviderSettings | None = None,
        cache: ProviderCache | None = None,
        usage: UsageTracker | None = None,
    ) -> None:
        self.settings = settings or get_provider_settings()
        self.cache = cache or ProviderCache(
            default_ttl_seconds=self.settings.cache_ttl_seconds
        )
        self.usage = usage or UsageTracker()
        self._providers: dict[ProviderName, Provider] = {
            ProviderName.MOCK: MockProvider(),
            ProviderName.GOOGLE_ADS: GoogleAdsProvider(self.settings),
            ProviderName.GOOGLE_TRENDS: GoogleTrendsProvider(self.settings),
            ProviderName.SERP: SerpProvider(self.settings),
            ProviderName.X_API: XApiProvider(self.settings),
            ProviderName.YOUTUBE: YouTubeProvider(self.settings),
        }

    def get(self, name: ProviderName | str) -> Provider:
        key = ProviderName(name) if isinstance(name, str) else name
        try:
            return self._providers[key]
        except KeyError as exc:
            raise KeyError(f"Unknown provider: {name}") from exc

    def list_status(self) -> list[ProviderStatus]:
        return [provider.status() for provider in self._providers.values()]

    def search(
        self,
        name: ProviderName | str,
        request: ProviderRequest,
        *,
        use_cache: bool | None = None,
    ) -> ProviderResponse:
        provider = self.get(name)
        cache_enabled = (
            self.settings.cache_enabled if use_cache is None else use_cache
        )
        cache_key = self.cache.make_key(provider.name, request)

        if cache_enabled:
            cached = self.cache.get(cache_key)
            if cached is not None:
                self.usage.record(
                    provider=provider.name,
                    operation="search",
                    mode=cached.mode,
                    success=True,
                    cached=True,
                    query=request.query,
                    details={"cache": "hit"},
                )
                return cached

        try:
            response = provider.search(request)
            success = True
        except Exception as exc:  # noqa: BLE001 — record failure then re-raise
            self.usage.record(
                provider=provider.name,
                operation="search",
                mode=provider.operating_mode(),
                success=False,
                cached=False,
                query=request.query,
                details={"error": str(exc)},
            )
            raise

        if cache_enabled and success:
            self.cache.set(cache_key, response)

        self.usage.record(
            provider=provider.name,
            operation="search",
            mode=response.mode,
            success=True,
            cached=False,
            query=request.query,
            details={"items": len(response.items)},
        )
        return response


@lru_cache
def get_registry() -> ProviderRegistry:
    return ProviderRegistry()


def reset_registry() -> None:
    get_registry.cache_clear()
