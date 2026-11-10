"""Pytest fixtures for GUM."""

from __future__ import annotations

import os
import sys

import pytest
from fastapi.testclient import TestClient

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


@pytest.fixture()
def client() -> TestClient:
    from app.db import reset_engine
    from app.main import create_app
    from providers.config import reset_provider_settings
    from providers.registry import reset_registry

    reset_provider_settings()
    reset_registry()
    reset_engine()
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
    reset_engine()
    reset_registry()
    reset_provider_settings()
