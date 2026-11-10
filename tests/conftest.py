"""Pytest fixtures for GUM."""

from __future__ import annotations

import os
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
API_ROOT = os.path.join(REPO_ROOT, "services", "api")
for path in (REPO_ROOT, API_ROOT):
    if path not in sys.path:
        sys.path.insert(0, path)

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg2://gum:gum@localhost:5432/gum_test",
)
os.environ.setdefault("CHECK_DB_ON_STARTUP", "false")
os.environ.setdefault("GUM_FORCE_MOCK_PROVIDERS", "true")

_TRUNCATE_SQL = """
TRUNCATE TABLE
  opportunities,
  evidence_clusters,
  opportunity_runs,
  pain_points,
  evidence_records,
  evidence_collections,
  provider_usage_events,
  provider_cache_entries,
  health_probes
RESTART IDENTITY CASCADE
"""


def _truncate_app_tables() -> None:
    from app.db import get_engine, reset_engine

    reset_engine()
    engine = get_engine()
    with engine.begin() as conn:
        # Tables may not all exist on older schemas; ignore missing ones.
        existing = {
            row[0]
            for row in conn.execute(
                text(
                    "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
                )
            )
        }
        targets = [
            "validation_experiments",
            "saved_opportunities",
            "opportunity_reports",
            "format_evaluations",
            "format_recommendations",
            "gap_findings",
            "competitors",
            "gap_reports",
            "opportunities",
            "evidence_clusters",
            "opportunity_runs",
            "pain_points",
            "evidence_collection_members",
            "evidence_records",
            "evidence_collections",
            "provider_usage_events",
            "provider_cache_entries",
            "health_probes",
        ]
        present = [t for t in targets if t in existing]
        if present:
            conn.execute(
                text(
                    "TRUNCATE TABLE "
                    + ", ".join(present)
                    + " RESTART IDENTITY CASCADE"
                )
            )


@pytest.fixture()
def client() -> TestClient:
    from app.db import reset_engine
    from app.main import create_app
    from providers.config import reset_provider_settings
    from providers.registry import reset_registry

    reset_provider_settings()
    reset_registry()
    _truncate_app_tables()
    reset_engine()
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
    reset_engine()
    reset_registry()
    reset_provider_settings()
