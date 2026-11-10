"""Runtime configuration for the GUM API."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "GUM API"
    environment: str = Field(default="development", alias="GUM_ENV")
    database_url: str = Field(
        default="postgresql+psycopg2://gum:gum@localhost:5432/gum",
        alias="DATABASE_URL",
    )
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
    )
    check_db_on_startup: bool = Field(default=True, alias="CHECK_DB_ON_STARTUP")

    # Provider infrastructure (Milestone 2) — mirrored for discoverability.
    force_mock_providers: bool = Field(default=True, alias="GUM_FORCE_MOCK_PROVIDERS")
    provider_cache_ttl_seconds: int = Field(
        default=300, alias="GUM_PROVIDER_CACHE_TTL_SECONDS"
    )
    provider_cache_enabled: bool = Field(
        default=True, alias="GUM_PROVIDER_CACHE_ENABLED"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


def reset_settings() -> None:
    get_settings.cache_clear()
