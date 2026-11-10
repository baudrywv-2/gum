"""Research platform selection (one / some / all) — Reddit ignored."""

from __future__ import annotations

from enum import Enum
from typing import Iterable

from pydantic import BaseModel, Field

from packages.contracts.claim_tags import ClaimTag
from packages.contracts.providers import ProviderMode, ProviderName


class ResearchPlatform(str, Enum):
    """User-facing platform ids for discover/research filters."""

    YOUTUBE = "youtube"
    SERP = "serp"
    TRENDS = "trends"
    X = "x"
    ALL = "all"


# Maps UI/API platform ids → (provider, role). Reddit intentionally omitted.
_PLATFORM_PROVIDER: dict[ResearchPlatform, tuple[ProviderName, str]] = {
    ResearchPlatform.YOUTUBE: (ProviderName.YOUTUBE, "search"),
    ResearchPlatform.SERP: (ProviderName.SERP, "search"),
    ResearchPlatform.TRENDS: (ProviderName.GOOGLE_TRENDS, "search"),
    ResearchPlatform.X: (ProviderName.X_API, "discussion"),
}

# Aliases accepted in API payloads (case-insensitive).
_ALIASES: dict[str, ResearchPlatform] = {
    "youtube": ResearchPlatform.YOUTUBE,
    "yt": ResearchPlatform.YOUTUBE,
    "serp": ResearchPlatform.SERP,
    "google": ResearchPlatform.SERP,
    "google_serp": ResearchPlatform.SERP,
    "trends": ResearchPlatform.TRENDS,
    "google_trends": ResearchPlatform.TRENDS,
    "x": ResearchPlatform.X,
    "x_api": ResearchPlatform.X,
    "twitter": ResearchPlatform.X,
    "all": ResearchPlatform.ALL,
}

DEFAULT_RESEARCH_PLATFORMS: list[ResearchPlatform] = [
    ResearchPlatform.TRENDS,
    ResearchPlatform.SERP,
    ResearchPlatform.YOUTUBE,
    ResearchPlatform.X,
]


class PlatformRunSummary(BaseModel):
    """What ran for one selected platform (evidence-first transparency)."""

    platform: str
    provider: ProviderName
    role: str
    mode: ProviderMode
    claim_tag: ClaimTag = ClaimTag.UNVERIFIED_CLAIM
    item_count: int = 0
    skipped: bool = False
    error: str | None = None
    notes: str | None = None


class ResolvedPlatforms(BaseModel):
    requested: list[str] = Field(default_factory=list)
    search: list[ProviderName] = Field(default_factory=list)
    discussion: list[ProviderName] = Field(default_factory=list)

    @property
    def include_search(self) -> bool:
        return bool(self.search)

    @property
    def include_discussions(self) -> bool:
        return bool(self.discussion)


def normalize_platform_token(raw: str) -> ResearchPlatform:
    key = raw.strip().lower().replace("-", "_").replace(" ", "_")
    if key not in _ALIASES:
        raise ValueError(
            f"Unknown research platform '{raw}'. "
            f"Use youtube, serp, trends, x, or all."
        )
    return _ALIASES[key]


def parse_platforms(
    platforms: str | Iterable[str] | None,
) -> list[ResearchPlatform]:
    """Parse API input into concrete platforms (never includes ALL)."""
    if platforms is None:
        return list(DEFAULT_RESEARCH_PLATFORMS)

    if isinstance(platforms, str):
        tokens = [platforms]
    else:
        tokens = list(platforms)

    if not tokens:
        return list(DEFAULT_RESEARCH_PLATFORMS)

    parsed = [normalize_platform_token(t) for t in tokens]
    if ResearchPlatform.ALL in parsed:
        return list(DEFAULT_RESEARCH_PLATFORMS)

    # Preserve order, unique
    seen: set[ResearchPlatform] = set()
    out: list[ResearchPlatform] = []
    for platform in parsed:
        if platform is ResearchPlatform.ALL:
            continue
        if platform in seen:
            continue
        seen.add(platform)
        out.append(platform)
    if not out:
        return list(DEFAULT_RESEARCH_PLATFORMS)
    return out


def resolve_platforms(
    platforms: str | Iterable[str] | None,
) -> ResolvedPlatforms:
    selected = parse_platforms(platforms)
    search: list[ProviderName] = []
    discussion: list[ProviderName] = []
    for platform in selected:
        provider, role = _PLATFORM_PROVIDER[platform]
        if role == "search":
            if provider not in search:
                search.append(provider)
        else:
            if provider not in discussion:
                discussion.append(provider)
    return ResolvedPlatforms(
        requested=[p.value for p in selected],
        search=search,
        discussion=discussion,
    )


def provider_to_platform(provider: ProviderName) -> str | None:
    for platform, (mapped, _role) in _PLATFORM_PROVIDER.items():
        if mapped is provider:
            return platform.value
    return None
