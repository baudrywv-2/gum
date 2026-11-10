"""Database connectivity and migration surface tests."""

from __future__ import annotations

from sqlalchemy import inspect, text

from app.db import check_database_connection, get_engine


def test_database_connects() -> None:
    check_database_connection()
    with get_engine().connect() as conn:
        value = conn.execute(text("SELECT 1")).scalar_one()
        assert value == 1


def test_health_probes_table_exists() -> None:
    inspector = inspect(get_engine())
    assert "health_probes" in inspector.get_table_names()
