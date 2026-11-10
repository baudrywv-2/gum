"""Milestone 9 MCP shared-ops tests (same engines as API)."""

from __future__ import annotations

import os
import sys

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MCP_ROOT = os.path.join(REPO_ROOT, "services", "mcp")
for path in (REPO_ROOT, os.path.join(REPO_ROOT, "services", "api"), MCP_ROOT):
    if path not in sys.path:
        sys.path.insert(0, path)


@pytest.fixture(autouse=True)
def _mcp_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CHECK_DB_ON_STARTUP", "false")
    monkeypatch.setenv("GUM_FORCE_MOCK_PROVIDERS", "true")


def test_mcp_tool_names_registered() -> None:
    from server import mcp

    tools = mcp._tool_manager.list_tools()
    names = {t.name for t in tools}
    required = {
        "discover_opportunities",
        "research_niche",
        "find_seo_gaps",
        "search_x_conversations",
        "extract_user_pain_points",
        "analyse_competitors",
        "compare_solution_formats",
        "score_opportunity",
        "validate_opportunity_across_sources",
        "generate_opportunity_report",
        "save_opportunity",
        "get_opportunity_details",
    }
    assert required <= names


def test_mcp_shared_ops_pipeline(client) -> None:
    """client fixture ensures DB/migrations + truncate; ops use same DB."""
    from shared_ops import (
        generate_opportunity_report,
        get_opportunity_details,
        save_opportunity,
        search_x_conversations,
    )

    x = search_x_conversations("freelancer invoicing", limit=3)
    assert x["provider"] == "x_api"
    assert isinstance(x.get("items"), list)

    report_payload = generate_opportunity_report(
        "freelancer invoicing calculator tool",
        geography="US",
        language="en",
    )
    assert report_payload["count"] >= 1
    report_id = report_payload["reports"][0]["id"]
    details = get_opportunity_details(report_id)
    assert details["id"] == report_id
    assert "scores" in details
    saved = save_opportunity(report_id, note="mcp test")
    assert saved["report_id"] == report_id
    assert saved["saved_id"]
