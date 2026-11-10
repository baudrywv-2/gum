"""Milestone 3 evidence collection tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from evidence.dedupe import evidence_fingerprint, normalize_text
from evidence.pain_points import extract_pain_points
from packages.contracts.claim_tags import ClaimTag
from packages.contracts.evidence import (
    EvidenceKind,
    EvidenceRecord,
    Provenance,
    ReliabilityLevel,
)
from packages.contracts.providers import ProviderMode, ProviderName
from datetime import datetime, timezone


def test_fingerprint_dedupes_identical_payloads() -> None:
    a = evidence_fingerprint(
        kind=EvidenceKind.SEARCH,
        provider=ProviderName.SERP,
        title="Hello World!",
        summary="Same summary",
        source_url="https://Example.INVALID/path",
    )
    b = evidence_fingerprint(
        kind=EvidenceKind.SEARCH,
        provider=ProviderName.SERP,
        title="hello world",
        summary="same   summary",
        source_url="https://example.invalid/path",
    )
    assert a == b
    assert normalize_text("  Foo-Bar  ") == "foo bar"


def test_pain_point_extraction_tags_ai_interpretation() -> None:
    record = EvidenceRecord(
        kind=EvidenceKind.DISCUSSION,
        title="Frustrated with invoicing tools",
        summary="I hate how hard it is to find a good invoicing tool.",
        fingerprint="abc",
        provenance=Provenance(
            provider=ProviderName.X_API,
            provider_mode=ProviderMode.MOCK,
            collected_at=datetime.now(timezone.utc),
            claim_tag=ClaimTag.UNVERIFIED_CLAIM,
            reliability=ReliabilityLevel.LOW,
        ),
    )
    pains = extract_pain_points([record])
    assert pains
    assert all(p.claim_tag is ClaimTag.AI_INTERPRETATION for p in pains)
    assert any("hate" in p.text.lower() or "hard" in p.text.lower() for p in pains)


def test_collect_evidence_api_persists_and_dedupes(client: TestClient) -> None:
    body = {
        "query": "freelancer invoicing",
        "geography": "US",
        "language": "en",
        "include_search": True,
        "include_discussions": True,
        "extract_pain_points": True,
        "limit_per_provider": 3,
    }
    first = client.post("/evidence/collect", json=body)
    assert first.status_code == 200, first.text
    payload = first.json()
    assert payload["evidence_created"] > 0
    assert payload["collection_id"]
    assert any(e["kind"] == "search" for e in payload["evidence"])
    assert any(e["kind"] == "discussion" for e in payload["evidence"])
    assert payload["pain_points_created"] + payload["pain_points_updated"] >= 1

    # Provenance preserved on every record
    for record in payload["evidence"]:
        prov = record["provenance"]
        assert prov["provider"]
        assert prov["provider_mode"] == "mock"
        assert prov["claim_tag"]
        assert prov["collected_at"]
        assert prov["query"] == "freelancer invoicing"
        assert isinstance(prov["limitations"], list)

    # Second identical collect should mostly dedupe fingerprints
    second = client.post("/evidence/collect", json=body)
    assert second.status_code == 200
    assert second.json()["evidence_deduplicated"] > 0

    listed = client.get("/evidence", params={"kind": "search"})
    assert listed.status_code == 200
    assert listed.json()["count"] >= 1

    discussions = client.get("/evidence", params={"kind": "discussion"})
    assert discussions.status_code == 200
    assert discussions.json()["count"] >= 1

    pains = client.get("/evidence/pain-points")
    assert pains.status_code == 200
    assert pains.json()["count"] >= 1
    assert all(
        p["claim_tag"] == "AI_INTERPRETATION" for p in pains.json()["pain_points"]
    )

    collection_id = payload["collection_id"]
    summary = client.get(f"/evidence/collections/{collection_id}")
    assert summary.status_code == 200
    assert summary.json()["query"] == "freelancer invoicing"
    assert summary.json()["evidence_count"] >= 1


def test_db_evidence_tables_exist(client: TestClient) -> None:
    from sqlalchemy import inspect

    from app.db import get_engine

    tables = set(inspect(get_engine()).get_table_names())
    assert "evidence_collections" in tables
    assert "evidence_records" in tables
    assert "pain_points" in tables
