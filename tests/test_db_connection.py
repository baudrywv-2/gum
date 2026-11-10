"""Database connectivity and migration surface tests."""

from __future__ import annotations

from sqlalchemy import inspect, text

from app.db import check_database_connection, get_engine


def test_database_connects() -> None:
    check_database_connection()
    with get_engine().connect() as conn:
        value = conn.execute(text("SELECT 1")).scalar_one()
        assert value == 1


def test_m1_m2_m3_tables_exist() -> None:
    inspector = inspect(get_engine())
    tables = set(inspector.get_table_names())
    assert "health_probes" in tables
    assert "provider_usage_events" in tables
    assert "provider_cache_entries" in tables
    assert "evidence_collections" in tables
    assert "evidence_records" in tables
    assert "pain_points" in tables

