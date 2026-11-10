"""Platform filter resolution and skip-unselected behavior."""

from __future__ import annotations

import pytest

from packages.contracts.platforms import (
    DEFAULT_RESEARCH_PLATFORMS,
    ResearchPlatform,
    parse_platforms,
    resolve_platforms,
)
from packages.contracts.providers import ProviderName


def test_default_platforms_are_live_set() -> None:
    resolved = resolve_platforms(None)
    assert resolved.requested == [p.value for p in DEFAULT_RESEARCH_PLATFORMS]
    assert ProviderName.SERP in resolved.search
    assert ProviderName.YOUTUBE in resolved.search
    assert ProviderName.GOOGLE_TRENDS in resolved.search
    assert ProviderName.X_API in resolved.discussion
    assert ProviderName.REDDIT not in resolved.search
    assert ProviderName.REDDIT not in resolved.discussion


def test_all_expands_to_default_set() -> None:
    assert parse_platforms("all") == list(DEFAULT_RESEARCH_PLATFORMS)
    assert parse_platforms(["all", "youtube"]) == list(DEFAULT_RESEARCH_PLATFORMS)


def test_single_and_combined_platforms() -> None:
    yt = resolve_platforms("youtube")
    assert yt.requested == ["youtube"]
    assert yt.search == [ProviderName.YOUTUBE]
    assert yt.discussion == []
    assert yt.include_search is True
    assert yt.include_discussions is False

    combo = resolve_platforms(["serp", "x"])
    assert combo.requested == ["serp", "x"]
    assert combo.search == [ProviderName.SERP]
    assert combo.discussion == [ProviderName.X_API]


def test_aliases_and_unknown() -> None:
    assert resolve_platforms(["google_trends", "twitter"]).requested == ["trends", "x"]
    with pytest.raises(ValueError, match="Unknown research platform"):
        resolve_platforms("reddit")


def test_collect_request_platforms_override_providers() -> None:
    from packages.contracts.evidence import CollectEvidenceRequest

    req = CollectEvidenceRequest(query="freelancer invoicing", platforms=["youtube"])
    assert req.platforms == ["youtube"]
    # defaults still present on model; collector applies override at runtime
    assert ProviderName.SERP in req.providers_search
