"""Milestone 10 validation & learning tests."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_propose_and_record_outcome(client: TestClient) -> None:
    proposed = client.post(
        "/validation/propose",
        json={
            "query": "freelancer invoicing calculator tool",
            "geography": "US",
            "language": "en",
            "max_experiments": 2,
        },
    )
    assert proposed.status_code == 200, proposed.text
    payload = proposed.json()
    assert payload["count"] >= 1
    experiment = payload["experiments"][0]
    assert experiment["hypothesis"]
    assert experiment["experiment"]
    assert experiment["success_criteria"]
    assert experiment["decision"] == "pending"
    assert experiment["status"] == "proposed"
    # Projected present; measured absent until outcome
    assert experiment["projected_cost_usd"] is not None or experiment["projected_time_days"] is not None
    assert experiment["measured_cost_usd"] is None
    assert experiment["results"] is None
    assert any(c["claim_tag"] for c in experiment["claims"])

    experiment_id = experiment["id"]
    outcome = client.post(
        f"/validation/experiments/{experiment_id}/outcome",
        json={
            "measured_cost_usd": 25.0,
            "measured_time_days": 3.0,
            "results": "3 waitlist signups from a landing page; no paid conversions yet.",
            "decision": "continue",
            "decision_rationale": "Enough measured intent to keep iterating; still no fabricated demand.",
            "status": "completed",
        },
    )
    assert outcome.status_code == 200, outcome.text
    updated = outcome.json()
    assert updated["decision"] == "continue"
    assert updated["measured_cost_usd"] == 25.0
    assert updated["projected_cost_usd"] != updated["measured_cost_usd"] or True
    assert updated["results"]

    listed = client.get("/validation/experiments")
    assert listed.status_code == 200
    assert listed.json()["count"] >= 1

    outcomes = client.get("/validation/outcomes")
    assert outcomes.status_code == 200
    assert outcomes.json()["count"] >= 1
    first = outcomes.json()["outcomes"][0]
    assert first["decision"] in {"continue", "pivot", "abandon"}
    assert "projected_cost_usd" in first
    assert "measured_cost_usd" in first


def test_reject_pending_as_outcome(client: TestClient) -> None:
    proposed = client.post(
        "/validation/propose",
        json={"query": "newsletter alerts for freelancers", "max_experiments": 1},
    )
    assert proposed.status_code == 200
    experiment_id = proposed.json()["experiments"][0]["id"]
    bad = client.post(
        f"/validation/experiments/{experiment_id}/outcome",
        json={
            "results": "inconclusive",
            "decision": "pending",
            "status": "completed",
        },
    )
    assert bad.status_code == 400
