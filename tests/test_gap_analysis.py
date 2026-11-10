"""Milestone 5 competitor / gap analysis tests."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from gap_engine.competitors import extract_competitors
from gap_engine.gaps import attach_feedback_to_competitors
from packages.contracts.claim_tags import ClaimTag
from packages.contracts.evidence import EvidenceKind, EvidenceRecord, Provenance, ReliabilityLevel
from packages.contracts.gaps import CompetitorStatus
from packages.contracts.providers import ProviderMode, ProviderName


def _evidence(
    *,
    kind: EvidenceKind,
    title: str,
    summary: str,
    provider: ProviderName,
    url: str | None = None,
) -> EvidenceRecord:
    return EvidenceRecord(
        id=uuid4(),
        kind=kind,
        title=title,
        summary=summary,
        fingerprint=str(uuid4()),
        provenance=Provenance(
            provider=provider,
            provider_mode=ProviderMode.MOCK,
            source_url=url,
            query="freelancer invoicing",
            collected_at=datetime.now(timezone.utc),
            claim_tag=ClaimTag.UNVERIFIED_CLAIM,
            reliability=ReliabilityLevel.LOW,
        ),
    )


def test_extract_competitors_from_search_only() -> None:
    evidence = [
        _evidence(
            kind=EvidenceKind.SEARCH,
            title="InvoiceBot — freelancer invoicing software",
            summary="listing",
            provider=ProviderName.SERP,
            url="https://invoicebot.example.invalid/x",
        ),
        _evidence(
            kind=EvidenceKind.DISCUSSION,
            title="random chat",
            summary="not a competitor source",
            provider=ProviderName.X_API,
        ),
    ]
    competitors = extract_competitors(evidence)
    assert competitors
    assert all(c.search_evidence_ids for c in competitors)
    assert all(c.status is CompetitorStatus.OBSERVED_IN_SEARCH for c in competitors)


def test_never_label_weak_without_complaint_evidence() -> None:
    search = _evidence(
        kind=EvidenceKind.SEARCH,
        title="Ledgerly Guide: invoicing",
        summary="guide",
        provider=ProviderName.SERP,
        url="https://ledgerly.example.invalid/guide",
    )
    mention_only = _evidence(
        kind=EvidenceKind.DISCUSSION,
        title="Tried Ledgerly today",
        summary="Neutral mention of Ledgerly without complaints.",
        provider=ProviderName.X_API,
    )
    competitors = attach_feedback_to_competitors(
        extract_competitors([search]), [search, mention_only]
    )
    ledgerly = next(c for c in competitors if "ledgerly" in c.name.casefold())
    assert ledgerly.status in {
        CompetitorStatus.MENTIONED_IN_FEEDBACK,
        CompetitorStatus.NO_WEAKNESS_EVIDENCE,
    }
    assert ledgerly.status is not CompetitorStatus.WEAKNESS_EVIDENCED
    assert not ledgerly.weaknesses


def test_weakness_requires_complaint_cues() -> None:
    search = _evidence(
        kind=EvidenceKind.SEARCH,
        title="InvoiceBot — invoicing",
        summary="listing",
        provider=ProviderName.SERP,
        url="https://invoicebot.example.invalid/x",
    )
    complaint = _evidence(
        kind=EvidenceKind.DISCUSSION,
        title="InvoiceBot issue",
        summary="Problem with InvoiceBot: too expensive and it fails to export CSV.",
        provider=ProviderName.X_API,
    )
    competitors = attach_feedback_to_competitors(
        extract_competitors([search]), [search, complaint]
    )
    bot = next(c for c in competitors if "invoicebot" in c.name.casefold())
    assert bot.status is CompetitorStatus.WEAKNESS_EVIDENCED
    assert bot.weaknesses
    assert all(w.claim_tag is ClaimTag.AI_INTERPRETATION for w in bot.weaknesses)
    assert all(w.evidence_ids for w in bot.weaknesses)


def test_analyze_gaps_api_evidence_backed(client: TestClient) -> None:
    response = client.post(
        "/gaps/analyze",
        json={
            "query": "freelancer invoicing",
            "geography": "US",
            "language": "en",
            "collect_if_missing": True,
        },
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    report = payload["report"]
    assert report["competitors"]
    assert report["search_vs_feedback"]
    assert report["missing_info"]

    # Competitors without complaint evidence must not be marked weakness_evidenced
    for competitor in report["competitors"]:
        assert competitor["claims"]
        if competitor["status"] == "weakness_evidenced":
            assert competitor["weaknesses"]
            assert competitor["feedback_evidence_ids"]
        else:
            # Explicitly not weak, or no evidence
            assert competitor["status"] in {
                "observed_in_search",
                "mentioned_in_feedback",
                "no_weakness_evidence",
            }

    for finding in report["findings"]:
        assert finding["claims"]
        for claim in finding["claims"]:
            assert claim["claim_tag"] in {
                "MEASURED_FACT",
                "PROVIDER_ESTIMATE",
                "AI_INTERPRETATION",
                "HYPOTHESIS",
                "UNVERIFIED_CLAIM",
            }
        blob = (finding["title"] + finding["summary"]).lower()
        assert "market share" not in blob
        assert "tam" not in blob

    listed = client.get("/gaps")
    assert listed.status_code == 200
    assert listed.json()["count"] >= 1

    detail = client.get(f"/gaps/{payload['report_id']}")
    assert detail.status_code == 200
    assert detail.json()["id"] == payload["report_id"]


def test_m5_tables_exist(client: TestClient) -> None:
    from sqlalchemy import inspect

    from app.db import get_engine

    tables = set(inspect(get_engine()).get_table_names())
    assert "gap_reports" in tables
    assert "competitors" in tables
    assert "gap_findings" in tables
