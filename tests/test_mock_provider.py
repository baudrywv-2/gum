"""Mock provider stub tests."""

from __future__ import annotations

from packages.contracts.claim_tags import ClaimTag
from packages.contracts.providers import ProviderMode, ProviderName, ProviderRequest
from providers.mock import MockProvider


def test_mock_provider_search() -> None:
    provider = MockProvider()
    result = provider.search(ProviderRequest(query="pain points around invoicing"))
    assert result.provider is ProviderName.MOCK
    assert result.mode is ProviderMode.MOCK
    assert result.claim_tag is ClaimTag.UNVERIFIED_CLAIM
    assert "invoicing" in result.summary
    assert result.raw["source"] == "mock"
    assert len(result.items) >= 1
