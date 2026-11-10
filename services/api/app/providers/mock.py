"""Mock provider used until real adapters land in Milestone 2+."""

from __future__ import annotations

from datetime import datetime, timezone

from packages.contracts.claim_tags import ClaimTag
from packages.contracts.providers import MockProviderResult, ProviderName


class MockProvider:
    name = ProviderName.MOCK

    def search(self, query: str) -> MockProviderResult:
        return MockProviderResult(
            provider=self.name,
            query=query,
            summary=f"Mock result for query: {query}",
            claim_tag=ClaimTag.UNVERIFIED_CLAIM,
            fetched_at=datetime.now(timezone.utc),
            raw={"source": "mock", "query": query},
        )
