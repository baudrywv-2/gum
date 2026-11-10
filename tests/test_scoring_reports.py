"""Milestone 7 scoring and reporting tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from packages.contracts.scoring import ScoreDimension
from scoring_engine.weights import DEFAULT_WEIGHTS


def test_weights_sum_to_one() -> None:
    total = sum(DEFAULT_WEIGHTS.values())
    assert abs(total - 1.0) < 1e-9
    assert ScoreDimension.OVERALL_PRIORITY not in DEFAULT_WEIGHTS


def test_generate_report_api(client: TestClient) -> None:
    response = client.post(
        "/reports/generate",
        json={
            "query": "freelancer invoicing calculator tool",
            "geography": "US",
            "language": "en",
            "collect_if_missing": True,
            "run_discovery": True,
            "run_gap_analysis": True,
            "run_format_recommendation": True,
        },
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["count"] >= 1
    report = payload["reports"][0]
    scores = report["scores"]
    for key in (
        "demand_evidence",
        "organic_ranking_feasibility",
        "format_fit",
        "business_viability",
        "evidence_confidence",
        "overall_priority",
    ):
        assert key in scores
        assert "explanation" in scores[key]
        assert 0.0 <= scores[key]["score"] <= 1.0
        assert scores[key]["claims"]

    # Required report fields
    for field in (
        "title",
        "summary",
        "problem",
        "demand_evidence",
        "discussion_evidence",
        "unmet_needs",
        "scores",
        "missing_info",
        "limitations",
        "next_actions",
    ):
        assert field in report

    # Never invent demand volumes in explanations
    blob = " ".join(
        [
            scores["demand_evidence"]["explanation"],
            scores["overall_priority"]["explanation"],
            *(c["text"] for c in scores["demand_evidence"]["claims"]),
        ]
    ).lower()
    assert "tam" not in blob
    assert "10,000 searches" not in blob

    # Overall cannot exceed confidence gate absurdly with evidence present
    assert scores["evidence_confidence"]["score"] > 0
    assert scores["overall_priority"]["score"] > 0

    listed = client.get("/reports")
    assert listed.status_code == 200
    assert listed.json()["count"] >= 1

    detail = client.get(f"/reports/{report['id']}")
    assert detail.status_code == 200
    assert detail.json()["id"] == report["id"]

    ranked = client.post(
        "/reports/rank",
        json={
            "rank_by": "overall_priority",
            "min_evidence_confidence": 0.0,
            "limit": 10,
        },
    )
    assert ranked.status_code == 200
    assert ranked.json()["count"] >= 1


def test_zero_evidence_confidence_gates_overall() -> None:
    from packages.contracts.opportunities import Opportunity, OpportunityType
    from scoring_engine.score import score_opportunity

    scores = score_opportunity(
        opportunity=None,
        query="empty",
        evidence=[],
        pain_points=[],
        gap_report=None,
        format_rec=None,
    )
    assert scores.evidence_confidence.score == 0.0
    assert scores.overall_priority.score == 0.0
    assert scores.demand_evidence.score == 0.0
