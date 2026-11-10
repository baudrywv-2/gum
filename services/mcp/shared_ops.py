"""Shared operations used by the MCP server (same engines as the HTTP API).

No duplicated intelligence logic — MCP is another interface over the engines.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from evidence.collector import EvidenceCollector
from evidence.store import EvidenceStore
from format_engine.recommend import FormatRecommender
from gap_engine.analyze import GapAnalysisEngine
from opportunity_engine.discover import OpportunityDiscoveryEngine
from packages.contracts.evidence import CollectEvidenceRequest
from packages.contracts.formats import RecommendFormatsRequest
from packages.contracts.gaps import AnalyzeGapsRequest
from packages.contracts.opportunities import DiscoverOpportunitiesRequest
from packages.contracts.providers import ProviderName, ProviderRequest
from packages.contracts.scoring import GenerateReportRequest
from providers.registry import get_registry
from scoring_engine.report import ReportEngine
from scoring_engine.store import ScoringStore


def _session() -> Session:
    from app.db import get_session_factory

    return get_session_factory()()


def discover_opportunities(
    query: str,
    geography: str | None = None,
    language: str | None = None,
) -> dict[str, Any]:
    session = _session()
    try:
        result = OpportunityDiscoveryEngine(session).discover(
            DiscoverOpportunitiesRequest(
                query=query,
                geography=geography,
                language=language,
            )
        )
        return result.model_dump(mode="json")
    finally:
        session.close()


def research_niche(
    query: str,
    geography: str | None = None,
    language: str | None = None,
) -> dict[str, Any]:
    """Collect evidence + discover opportunities for a niche (shared engines)."""
    session = _session()
    try:
        collected = EvidenceCollector(session).collect(
            CollectEvidenceRequest(
                query=query,
                geography=geography,
                language=language,
            )
        )
        discovered = OpportunityDiscoveryEngine(session).discover(
            DiscoverOpportunitiesRequest(
                query=query,
                geography=geography,
                language=language,
                collection_id=collected.collection_id,
                collect_if_missing=False,
            )
        )
        return {
            "collection": collected.model_dump(mode="json"),
            "discovery": discovered.model_dump(mode="json"),
            "limitations": list(
                dict.fromkeys(collected.limitations + discovered.limitations)
            ),
        }
    finally:
        session.close()


def find_seo_gaps(
    query: str,
    geography: str | None = None,
    language: str | None = None,
) -> dict[str, Any]:
    session = _session()
    try:
        result = GapAnalysisEngine(session).analyze(
            AnalyzeGapsRequest(
                query=query,
                geography=geography,
                language=language,
            )
        )
        report = result.report
        content_gaps = [
            f.model_dump(mode="json")
            for f in report.findings
            if f.kind.value == "missing_content"
        ]
        return {
            "report_id": str(result.report_id),
            "content_gaps": content_gaps,
            "competitors": [c.model_dump(mode="json") for c in report.competitors],
            "limitations": result.limitations,
        }
    finally:
        session.close()


def search_x_conversations(
    query: str,
    geography: str | None = None,
    language: str | None = None,
    limit: int = 5,
) -> dict[str, Any]:
    registry = get_registry()
    response = registry.search(
        ProviderName.X_API,
        ProviderRequest(
            query=query,
            geography=geography,
            language=language,
            limit=limit,
        ),
    )
    return response.model_dump(mode="json")


def extract_user_pain_points(
    query: str,
    geography: str | None = None,
    language: str | None = None,
) -> dict[str, Any]:
    session = _session()
    try:
        collected = EvidenceCollector(session).collect(
            CollectEvidenceRequest(
                query=query,
                geography=geography,
                language=language,
            )
        )
        pains = EvidenceStore(session).list_pain_points(
            collection_id=collected.collection_id, limit=100
        )
        return {
            "collection_id": str(collected.collection_id),
            "pain_points": [p.model_dump(mode="json") for p in pains],
            "limitations": collected.limitations,
        }
    finally:
        session.close()


def analyse_competitors(
    query: str,
    geography: str | None = None,
    language: str | None = None,
) -> dict[str, Any]:
    session = _session()
    try:
        result = GapAnalysisEngine(session).analyze(
            AnalyzeGapsRequest(
                query=query,
                geography=geography,
                language=language,
            )
        )
        return result.model_dump(mode="json")
    finally:
        session.close()


def compare_solution_formats(
    query: str,
    geography: str | None = None,
    language: str | None = None,
) -> dict[str, Any]:
    session = _session()
    try:
        result = FormatRecommender(session).recommend(
            RecommendFormatsRequest(
                query=query,
                geography=geography,
                language=language,
            )
        )
        return result.model_dump(mode="json")
    finally:
        session.close()


def score_opportunity(
    query: str,
    geography: str | None = None,
    language: str | None = None,
) -> dict[str, Any]:
    session = _session()
    try:
        result = ReportEngine(session).generate(
            GenerateReportRequest(
                query=query,
                geography=geography,
                language=language,
            )
        )
        return {
            "count": result.count,
            "ranked_by": result.ranked_by.value,
            "reports": [
                {
                    "id": str(r.id),
                    "title": r.title,
                    "scores": r.scores.model_dump(mode="json"),
                    "recommended_format": (
                        r.recommended_format.value if r.recommended_format else None
                    ),
                }
                for r in result.reports
            ],
            "limitations": result.limitations,
        }
    finally:
        session.close()


def validate_opportunity_across_sources(
    query: str,
    geography: str | None = None,
    language: str | None = None,
) -> dict[str, Any]:
    """Cross-source correlation via discovery engine (shared logic)."""
    session = _session()
    try:
        result = OpportunityDiscoveryEngine(session).discover(
            DiscoverOpportunitiesRequest(
                query=query,
                geography=geography,
                language=language,
            )
        )
        return {
            "correlations": [c.model_dump(mode="json") for c in result.correlations],
            "emerging_themes": [
                t.model_dump(mode="json") for t in result.emerging_themes
            ],
            "collection_id": str(result.collection_id),
            "limitations": result.limitations
            + [
                "Cross-source validation correlates independent evidence; "
                "it does not invent agreement where sources diverge."
            ],
        }
    finally:
        session.close()


def generate_opportunity_report(
    query: str,
    geography: str | None = None,
    language: str | None = None,
) -> dict[str, Any]:
    session = _session()
    try:
        result = ReportEngine(session).generate(
            GenerateReportRequest(
                query=query,
                geography=geography,
                language=language,
            )
        )
        return result.model_dump(mode="json")
    finally:
        session.close()


def save_opportunity(report_id: str, note: str | None = None) -> dict[str, Any]:
    session = _session()
    try:
        from database.models import SavedOpportunityRow

        rid = uuid.UUID(report_id)
        report = ScoringStore(session).get_report(rid)
        if report is None:
            raise ValueError(f"Unknown report_id: {report_id}")
        row = SavedOpportunityRow(
            id=uuid.uuid4(),
            report_id=rid,
            query=report.query,
            title=report.title,
            note=note,
            attributes={"source": "mcp"},
        )
        session.add(row)
        session.commit()
        return {
            "saved_id": str(row.id),
            "report_id": report_id,
            "title": report.title,
            "note": note,
        }
    finally:
        session.close()


def get_opportunity_details(report_id: str) -> dict[str, Any]:
    session = _session()
    try:
        report = ScoringStore(session).get_report(uuid.UUID(report_id))
        if report is None:
            raise ValueError(f"Unknown report_id: {report_id}")
        return report.model_dump(mode="json")
    finally:
        session.close()
