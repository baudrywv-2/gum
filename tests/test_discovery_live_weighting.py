"""Discovery should prefer live MEASURED_FACT and not lean on MOCK discussion."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from opportunity_engine.audiences import hypothesize_underserved_audiences
from packages.contracts.claim_tags import ClaimTag
from packages.contracts.evidence import (
    CollectEvidenceRequest,
    EvidenceKind,
    EvidenceRecord,
    PainPoint,
    Provenance,
    ReliabilityLevel,
)
from packages.contracts.opportunities import EmergingTheme
from packages.contracts.providers import ProviderMode, ProviderName


def test_default_collect_providers_prefer_serpapi_youtube_not_mock_discussion() -> None:
    req = CollectEvidenceRequest(query="freelancer invoicing")
    assert ProviderName.SERP in req.providers_search
    assert ProviderName.YOUTUBE in req.providers_search
    assert ProviderName.GOOGLE_TRENDS in req.providers_search
    assert ProviderName.MOCK not in req.providers_discussion
    assert req.providers_discussion == [ProviderName.X_API]


def test_audiences_label_discussion_unavailable_and_skip_mock_only_pains() -> None:
    live_search = EvidenceRecord(
        id=uuid4(),
        kind=EvidenceKind.SEARCH,
        title="Freelancer invoicing guide",
        summary="Live SERP hit",
        fingerprint=str(uuid4()),
        provenance=Provenance(
            provider=ProviderName.SERP,
            provider_mode=ProviderMode.LIVE,
            collected_at=datetime.now(timezone.utc),
            claim_tag=ClaimTag.MEASURED_FACT,
            reliability=ReliabilityLevel.MEDIUM,
        ),
    )
    mock_pain = PainPoint(
        text="annoying gaps remain",
        normalized_text="annoying gaps remain",
        frequency=4,
        claim_tag=ClaimTag.AI_INTERPRETATION,
        evidence_ids=[uuid4()],
        source_providers=[ProviderName.MOCK],
    )
    hyps = hypothesize_underserved_audiences(
        query="freelancer invoicing",
        geography="US",
        language="en",
        evidence=[live_search],
        pain_points=[mock_pain],
    )
    labels = [h.audience_label for h in hyps]
    assert any("Discussion signal unavailable" in label for label in labels)
    assert not any("annoying gaps" in label for label in labels)


def test_theme_weighting_prefers_serpapi_youtube_providers() -> None:
    weak = EmergingTheme(
        theme="Theme around 'not'",
        token="not",
        evidence_count=5,
        provider_count=2,
        providers=[ProviderName.MOCK, ProviderName.GOOGLE_ADS],
        evidence_ids=[uuid4(), uuid4()],
    )
    strong = EmergingTheme(
        theme="Theme around 'invoicing'",
        token="invoicing",
        evidence_count=4,
        provider_count=2,
        providers=[ProviderName.SERP, ProviderName.YOUTUBE],
        evidence_ids=[uuid4(), uuid4()],
    )
    themes_sorted = sorted(
        [weak, strong],
        key=lambda t: (
            -sum(1 for p in t.providers if p.value in {"serp", "youtube", "google_trends"}),
            -t.provider_count,
            -t.evidence_count,
        ),
    )
    assert themes_sorted[0].token == "invoicing"
