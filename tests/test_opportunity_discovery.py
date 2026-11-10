"""Milestone 4 opportunity discovery tests."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from opportunity_engine.cluster import cluster_evidence
from opportunity_engine.themes import detect_emerging_themes
from packages.contracts.claim_tags import ClaimTag
from packages.contracts.evidence import EvidenceKind, EvidenceRecord, Provenance, ReliabilityLevel
from packages.contracts.opportunities import OpportunityType
from packages.contracts.providers import ProviderMode, ProviderName


def _record(
    *,
    title: str,
    summary: str,
    kind: EvidenceKind,
    provider: ProviderName,
    query: str = "freelancer invoicing",
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
            query=query,
            collected_at=datetime.now(timezone.utc),
            claim_tag=ClaimTag.UNVERIFIED_CLAIM,
            reliability=ReliabilityLevel.LOW,
        ),
    )


def test_cluster_related_evidence() -> None:
    evidence = [
        _record(
            title="invoicing tools frustrated freelancers",
            summary="hard to find good invoicing",
            kind=EvidenceKind.DISCUSSION,
            provider=ProviderName.X_API,
        ),
        _record(
            title="freelancer invoicing keyword idea",
            summary="invoicing for freelancers",
            kind=EvidenceKind.SEARCH,
            provider=ProviderName.GOOGLE_ADS,
        ),
        _record(
            title="unrelated gardening tips",
            summary="plant watering schedules",
            kind=EvidenceKind.SEARCH,
            provider=ProviderName.SERP,
        ),
    ]
    clusters = cluster_evidence(evidence, min_cluster_size=2, similarity_threshold=0.15)
    assert clusters
    assert all(c.claim_tag is ClaimTag.AI_INTERPRETATION for c in clusters)
    assert any(c.size >= 2 for c in clusters)


def test_emerging_themes_require_multi_provider() -> None:
    evidence = [
        _record(
            title="invoicing automation",
            summary="automation for invoices",
            kind=EvidenceKind.SEARCH,
            provider=ProviderName.SERP,
        ),
        _record(
            title="automation pain invoicing",
            summary="automation is broken for invoices",
            kind=EvidenceKind.DISCUSSION,
            provider=ProviderName.X_API,
        ),
    ]
    themes = detect_emerging_themes(evidence, min_evidence=2, min_providers=2)
    assert themes
    assert all(t.claim_tag is ClaimTag.AI_INTERPRETATION for t in themes)
    assert all(t.provider_count >= 2 for t in themes)


def test_discover_api_labels_claims_and_avoids_fabricated_demand(
    client: TestClient,
) -> None:
    response = client.post(
        "/opportunities/discover",
        json={
            "query": "freelancer invoicing",
            "geography": "US",
            "language": "en",
            "collect_if_missing": True,
            "min_cluster_size": 1,
            "max_opportunities": 50,
        },
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["run_id"]
    assert payload["collection_id"]
    assert payload["opportunities"]
    types = {o["opportunity_type"] for o in payload["opportunities"]}
    assert OpportunityType.RECURRING_PROBLEM.value in types
    assert OpportunityType.UNDERSERVED_AUDIENCE.value in types
    # Interleaved selection should surface more than one discovery mode
    assert len(types) >= 2

    # Every opportunity claim is labeled and grounded; no fabricated volume fields
    for opp in payload["opportunities"]:
        assert opp["claims"]
        for claim in opp["claims"]:
            assert claim["claim_tag"] in {
                "MEASURED_FACT",
                "PROVIDER_ESTIMATE",
                "AI_INTERPRETATION",
                "HYPOTHESIS",
                "UNVERIFIED_CLAIM",
            }
        # Recurring / audience / cross-source should cite stored evidence IDs
        if opp["opportunity_type"] != "emerging_theme":
            assert opp["evidence_ids"] or any(
                c.get("evidence_ids") for c in opp["claims"]
            )
        assert opp["missing_info"]
        blob = (opp["summary"] + " " + opp["title"]).lower()
        assert "tam" not in blob
        assert "10,000 searches" not in blob
        assert "monthly searches: 5000" not in blob


    # Underserved audiences are hypotheses
    assert payload["underserved_audiences"]
    assert all(
        a["claim_tag"] == "HYPOTHESIS" for a in payload["underserved_audiences"]
    )

    # Limitations state no fabricated demand
    assert any("fabricated" in line.lower() or "not measured" in line.lower() or "mock" in line.lower() for line in payload["limitations"])

    listed = client.get("/opportunities", params={"run_id": payload["run_id"]})
    assert listed.status_code == 200
    assert listed.json()["count"] >= 1

    summary = client.get(f"/opportunities/runs/{payload['run_id']}")
    assert summary.status_code == 200
    assert summary.json()["opportunity_count"] >= 1


def test_m4_tables_exist(client: TestClient) -> None:
    from sqlalchemy import inspect

    from app.db import get_engine

    tables = set(inspect(get_engine()).get_table_names())
    assert "opportunity_runs" in tables
    assert "evidence_clusters" in tables
    assert "opportunities" in tables
