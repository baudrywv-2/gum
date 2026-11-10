"""Health-check endpoint tests."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_returns_ok_when_db_available(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["service"] == "gum-api"
    assert payload["version"] == "0.1.0"
    assert payload["status"] in {"ok", "degraded"}
    assert payload["database"] in {"connected", "unreachable"}
    assert "timestamp" in payload
    # With local Postgres + migrations, expect connected.
    assert payload["status"] == "ok"
    assert payload["database"] == "connected"
