"""Mock provider stub tests."""

from __future__ import annotations

from app.providers.mock import MockProvider
from packages.contracts.claim_tags import ClaimTag
from packages.contracts.providers import ProviderName


def test_mock_provider_search() -> None:
    provider = MockProvider()
    result = provider.search("pain points around invoicing")
    assert result.provider is ProviderName.MOCK
    assert result.claim_tag is ClaimTag.UNVERIFIED_CLAIM
    assert "invoicing" in result.summary
    assert result.raw["source"] == "mock"
