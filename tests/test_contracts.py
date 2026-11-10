"""Shared contract smoke tests."""

from __future__ import annotations

from datetime import datetime, timezone

from packages.contracts import ClaimTag, MockProviderResult, ProviderName
from packages.contracts.health import HealthStatus
from packages.contracts.providers import ProviderMode, ProviderRequest, ProviderResponse


def test_claim_tags_cover_brief_vocabulary() -> None:
    assert ClaimTag.MEASURED_FACT.value == "MEASURED_FACT"
    assert ClaimTag.PROVIDER_ESTIMATE.value == "PROVIDER_ESTIMATE"
    assert ClaimTag.AI_INTERPRETATION.value == "AI_INTERPRETATION"
    assert ClaimTag.HYPOTHESIS.value == "HYPOTHESIS"
    assert ClaimTag.UNVERIFIED_CLAIM.value == "UNVERIFIED_CLAIM"


def test_mock_provider_result_round_trip() -> None:
    result = MockProviderResult(
        provider=ProviderName.MOCK,
        mode=ProviderMode.MOCK,
        query="underserved niches",
        summary="stub",
        claim_tag=ClaimTag.UNVERIFIED_CLAIM,
        fetched_at=datetime.now(timezone.utc),
        raw={"ok": True},
    )
    dumped = result.model_dump()
    restored = MockProviderResult.model_validate(dumped)
    assert restored.query == "underserved niches"
    assert restored.provider is ProviderName.MOCK


def test_provider_request_and_response() -> None:
    request = ProviderRequest(query="seo gaps", limit=5)
    response = ProviderResponse(
        provider=ProviderName.SERP,
        mode=ProviderMode.MOCK,
        query=request.query,
        summary="mocked",
        claim_tag=ClaimTag.UNVERIFIED_CLAIM,
        fetched_at=datetime.now(timezone.utc),
        limitations=["stub"],
    )
    assert response.mode is ProviderMode.MOCK
    assert request.limit == 5


def test_health_status_contract() -> None:
    status = HealthStatus(
        status="ok",
        service="gum-api",
        version="0.2.0",
        database="connected",
        timestamp=datetime.now(timezone.utc),
    )
    assert status.service == "gum-api"


def test_evidence_contracts_export() -> None:
    from packages.contracts import EvidenceKind, Provenance, ReliabilityLevel

    assert EvidenceKind.SEARCH.value == "search"
    assert ReliabilityLevel.LOW.value == "low"
    assert Provenance.model_fields["claim_tag"]

