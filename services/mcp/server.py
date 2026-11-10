"""GUM Cursor MCP server — tools share backend engines with the HTTP API."""

from __future__ import annotations

import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
API_ROOT = os.path.join(REPO_ROOT, "services", "api")
MCP_ROOT = os.path.dirname(__file__)
for path in (REPO_ROOT, API_ROOT, MCP_ROOT):
    if path not in sys.path:
        sys.path.insert(0, path)

os.environ.setdefault("CHECK_DB_ON_STARTUP", "false")
os.environ.setdefault("GUM_FORCE_MOCK_PROVIDERS", "true")

from mcp.server.fastmcp import FastMCP

from shared_ops import (
    analyse_competitors,
    compare_solution_formats,
    discover_opportunities,
    extract_user_pain_points,
    find_seo_gaps,
    generate_opportunity_report,
    get_opportunity_details,
    research_niche,
    save_opportunity,
    score_opportunity,
    search_x_conversations,
    validate_opportunity_across_sources,
)

mcp = FastMCP(
    "gum",
    instructions=(
        "GUM Opportunity Intelligence Engine. Discover problems, collect evidence, "
        "and recommend formats with labeled claims. Never invent demand volumes. "
        "Mock providers are used unless live credentials are configured."
    ),
)


@mcp.tool(name="discover_opportunities")
def discover_opportunities_tool(
    query: str,
    geography: str | None = None,
    language: str | None = None,
) -> dict:
    """Discover recurring problems, themes, audiences, and cross-source opportunities."""
    return discover_opportunities(query, geography, language)


@mcp.tool(name="research_niche")
def research_niche_tool(
    query: str,
    geography: str | None = None,
    language: str | None = None,
) -> dict:
    """Research a niche: collect evidence then discover opportunities."""
    return research_niche(query, geography, language)


@mcp.tool(name="find_seo_gaps")
def find_seo_gaps_tool(
    query: str,
    geography: str | None = None,
    language: str | None = None,
) -> dict:
    """Find SEO/content gaps via competitor and gap analysis (evidence-backed)."""
    return find_seo_gaps(query, geography, language)


@mcp.tool(name="search_x_conversations")
def search_x_conversations_tool(
    query: str,
    geography: str | None = None,
    language: str | None = None,
    limit: int = 5,
) -> dict:
    """Search X conversations (mock unless credentials). Discovery signal only."""
    return search_x_conversations(query, geography, language, limit)


@mcp.tool(name="extract_user_pain_points")
def extract_user_pain_points_tool(
    query: str,
    geography: str | None = None,
    language: str | None = None,
) -> dict:
    """Collect evidence and extract labeled user pain points."""
    return extract_user_pain_points(query, geography, language)


@mcp.tool(name="analyse_competitors")
def analyse_competitors_tool(
    query: str,
    geography: str | None = None,
    language: str | None = None,
) -> dict:
    """Analyse competitors and gaps. Never labels weakness without evidence."""
    return analyse_competitors(query, geography, language)


@mcp.tool(name="compare_solution_formats")
def compare_solution_formats_tool(
    query: str,
    geography: str | None = None,
    language: str | None = None,
) -> dict:
    """Compare solution formats; prefer simple when evidence supports it."""
    return compare_solution_formats(query, geography, language)


@mcp.tool(name="score_opportunity")
def score_opportunity_tool(
    query: str,
    geography: str | None = None,
    language: str | None = None,
) -> dict:
    """Score opportunities across independent transparent dimensions."""
    return score_opportunity(query, geography, language)


@mcp.tool(name="validate_opportunity_across_sources")
def validate_opportunity_across_sources_tool(
    query: str,
    geography: str | None = None,
    language: str | None = None,
) -> dict:
    """Validate an opportunity by correlating independent evidence sources."""
    return validate_opportunity_across_sources(query, geography, language)


@mcp.tool(name="generate_opportunity_report")
def generate_opportunity_report_tool(
    query: str,
    geography: str | None = None,
    language: str | None = None,
) -> dict:
    """Generate structured opportunity reports with scores and labeled claims."""
    return generate_opportunity_report(query, geography, language)


@mcp.tool(name="save_opportunity")
def save_opportunity_tool(report_id: str, note: str | None = None) -> dict:
    """Save a scored opportunity report for later retrieval."""
    return save_opportunity(report_id, note)


@mcp.tool(name="get_opportunity_details")
def get_opportunity_details_tool(report_id: str) -> dict:
    """Get full details for a scored opportunity report."""
    return get_opportunity_details(report_id)


if __name__ == "__main__":
    mcp.run(transport="stdio")
