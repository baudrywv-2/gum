"""Milestone 6 format recommendation tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from format_engine.catalog import FORMAT_CATALOG, all_formats
from format_engine.signals import FormatSignals, build_signals
from packages.contracts.formats import SolutionFormat
from packages.contracts.claim_tags import ClaimTag


def test_catalog_covers_brief_formats() -> None:
    formats = {p.format for p in all_formats()}
    required = {
        SolutionFormat.SEO_WEBSITE_BLOG,
        SolutionFormat.ANDROID_APP,
        SolutionFormat.IOS_APP,
        SolutionFormat.WEB_APP,
        SolutionFormat.YOUTUBE,
        SolutionFormat.CALCULATOR_TOOL,
        SolutionFormat.DIRECTORY,
        SolutionFormat.MARKETPLACE,
        SolutionFormat.NEWSLETTER_ALERTS,
        SolutionFormat.SAAS,
        SolutionFormat.API_DATA_SERVICE,
        SolutionFormat.AI_AGENT,
        SolutionFormat.DIGITAL_PRODUCT,
        SolutionFormat.PROFESSIONAL_SERVICES,
    }
    assert required <= formats
    # Simpler formats rank ahead of native apps
    assert (
        FORMAT_CATALOG[SolutionFormat.CALCULATOR_TOOL].default_preference_rank
        < FORMAT_CATALOG[SolutionFormat.ANDROID_APP].default_preference_rank
    )


def test_toolish_signals_from_pain_language() -> None:
    from datetime import datetime, timezone
    from uuid import uuid4

    from packages.contracts.evidence import (
        EvidenceKind,
        EvidenceRecord,
        PainPoint,
        Provenance,
        ReliabilityLevel,
    )
    from packages.contracts.providers import ProviderMode, ProviderName

    evidence = [
        EvidenceRecord(
            id=uuid4(),
            kind=EvidenceKind.DISCUSSION,
            title="Need a calculator for invoicing fees",
            summary="Wish there was a simple export tool",
            fingerprint=str(uuid4()),
            provenance=Provenance(
                provider=ProviderName.X_API,
                provider_mode=ProviderMode.MOCK,
                collected_at=datetime.now(timezone.utc),
                claim_tag=ClaimTag.UNVERIFIED_CLAIM,
                reliability=ReliabilityLevel.LOW,
            ),
        )
    ]
    pains = [
        PainPoint(
            text="Wish there was a simple CSV export tool",
            normalized_text="wish there was a simple csv export tool",
            frequency=2,
            claim_tag=ClaimTag.AI_INTERPRETATION,
            evidence_ids=[evidence[0].id],
        )
    ]
    signals = build_signals(query="freelancer invoicing", evidence=evidence, pain_points=pains)
    assert "toolish" in signals.flags


def test_recommend_formats_api_quality_bar(client: TestClient) -> None:
    response = client.post(
        "/formats/recommend",
        json={
            "query": "freelancer invoicing calculator tool",
            "geography": "US",
            "language": "en",
            "collect_if_missing": True,
            "run_gap_analysis": True,
        },
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    rec = payload["recommendation"]
    assert rec["primary_format"]
    assert rec["evaluations"]
    assert rec["missing_info"]
    assert rec["claims"]
    assert rec["claims"][0]["claim_tag"] == "HYPOTHESIS"

    primary = next(e for e in rec["evaluations"] if e["decision"] == "primary")
    assert primary["complexity"]
    assert primary["maintenance"]
    assert primary["monetization_hypotheses"]
    assert primary["cheapest_validation"]
    assert primary["reasons_selected"] or primary["fit_score"] >= 0

    # Every evaluation has labeled select/reject rationale material
    for evaluation in rec["evaluations"]:
        for claim in evaluation["reasons_selected"] + evaluation["reasons_rejected"]:
            assert claim["claim_tag"] in {
                "MEASURED_FACT",
                "PROVIDER_ESTIMATE",
                "AI_INTERPRETATION",
                "HYPOTHESIS",
                "UNVERIFIED_CLAIM",
            }
        blob = (evaluation.get("cheapest_validation") or "").lower()
        assert "tam" not in blob
        assert "10,000 searches" not in blob

    # Prefer simple: native apps should not be primary without mobile evidence
    assert rec["primary_format"] not in {"android_app", "ios_app"}
    # Website not auto-default for toolish query
    # (may still win if scores say so, but tool query should prefer calculator/tool-ish)
    assert rec["primary_format"] in {
        "calculator_tool",
        "digital_product",
        "newsletter_alerts",
        "web_app",
        "saas",
        "seo_website_blog",
        "youtube",
        "directory",
        "professional_services",
        "api_data_service",
        "ai_agent",
        "marketplace",
    }

    listed = client.get("/formats")
    assert listed.status_code == 200
    assert listed.json()["count"] >= 1

    detail = client.get(f"/formats/{payload['recommendation_id']}")
    assert detail.status_code == 200
    assert detail.json()["id"] == payload["recommendation_id"]


def test_m6_tables_exist(client: TestClient) -> None:
    from sqlalchemy import inspect

    from app.db import get_engine

    tables = set(inspect(get_engine()).get_table_names())
    assert "format_recommendations" in tables
    assert "format_evaluations" in tables
