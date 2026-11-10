"""Persist opportunity scores and reports."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import OpportunityReportRow
from packages.contracts.claim_tags import ClaimTag
from packages.contracts.formats import SolutionFormat
from packages.contracts.opportunities import LabeledClaim
from packages.contracts.scoring import (
    OpportunityReport,
    OpportunityScores,
    ScoreDimension,
    ScoreExplanation,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _parse_claims(raw: list) -> list[LabeledClaim]:
    claims: list[LabeledClaim] = []
    for item in raw or []:
        try:
            evidence_ids = []
            for eid in item.get("evidence_ids") or []:
                try:
                    evidence_ids.append(uuid.UUID(str(eid)))
                except ValueError:
                    continue
            claims.append(
                LabeledClaim(
                    text=item["text"],
                    claim_tag=ClaimTag(item["claim_tag"]),
                    evidence_ids=evidence_ids,
                )
            )
        except (KeyError, ValueError):
            continue
    return claims


def _parse_uuids(values: list) -> list[uuid.UUID]:
    out: list[uuid.UUID] = []
    for value in values or []:
        try:
            out.append(uuid.UUID(str(value)))
        except ValueError:
            continue
    return out


def _parse_score(raw: dict) -> ScoreExplanation:
    return ScoreExplanation(
        dimension=ScoreDimension(raw["dimension"]),
        score=float(raw["score"]),
        weight=float(raw.get("weight") or 0.0),
        explanation=raw.get("explanation") or "",
        claims=_parse_claims(raw.get("claims") or []),
        evidence_ids=_parse_uuids(raw.get("evidence_ids") or []),
        inputs=dict(raw.get("inputs") or {}),
        limitations=list(raw.get("limitations") or []),
    )


def _parse_scores(raw: dict) -> OpportunityScores:
    return OpportunityScores(
        demand_evidence=_parse_score(raw["demand_evidence"]),
        organic_ranking_feasibility=_parse_score(raw["organic_ranking_feasibility"]),
        format_fit=_parse_score(raw["format_fit"]),
        business_viability=_parse_score(raw["business_viability"]),
        evidence_confidence=_parse_score(raw["evidence_confidence"]),
        overall_priority=_parse_score(raw["overall_priority"]),
    )


class ScoringStore:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save_report(self, report: OpportunityReport) -> OpportunityReport:
        report_id = report.id or uuid.uuid4()
        row = OpportunityReportRow(
            id=report_id,
            collection_id=report.collection_id,
            query=report.query,
            title=report.title,
            summary=report.summary,
            problem=report.problem,
            audience=report.audience,
            geography=report.geography,
            language=report.language,
            demand_evidence=[c.model_dump(mode="json") for c in report.demand_evidence],
            search_behaviour_keywords=list(report.search_behaviour_keywords),
            discussion_evidence=[
                c.model_dump(mode="json") for c in report.discussion_evidence
            ],
            competitors=list(report.competitors),
            competitor_weaknesses=[
                c.model_dump(mode="json") for c in report.competitor_weaknesses
            ],
            unmet_needs=[c.model_dump(mode="json") for c in report.unmet_needs],
            recommended_format=(
                report.recommended_format.value if report.recommended_format else None
            ),
            alternative_formats=[f.value for f in report.alternative_formats],
            scores=report.scores.model_dump(mode="json"),
            complexity=report.complexity,
            build_maintenance=report.build_maintenance,
            monetization_hypotheses=list(report.monetization_hypotheses),
            risks=[c.model_dump(mode="json") for c in report.risks],
            source_urls=list(report.source_urls),
            timestamps={
                k: (v.isoformat() if v is not None else None)
                for k, v in report.timestamps.items()
            },
            limitations=list(report.limitations),
            contradictions=list(report.contradictions),
            missing_info=list(report.missing_info),
            cheapest_validation_experiment=report.cheapest_validation_experiment,
            next_actions=list(report.next_actions),
            claims=[c.model_dump(mode="json") for c in report.claims],
            evidence_ids=[str(i) for i in report.evidence_ids],
            opportunity_ids=[str(i) for i in report.opportunity_ids],
            format_recommendation_id=report.format_recommendation_id,
            gap_report_id=report.gap_report_id,
            attributes=dict(report.attributes),
            created_at=_utcnow(),
        )
        self.session.add(row)
        self.session.flush()
        return report.model_copy(update={"id": report_id, "created_at": row.created_at})

    def get_report(self, report_id: uuid.UUID) -> OpportunityReport | None:
        row = self.session.get(OpportunityReportRow, report_id)
        if row is None:
            return None
        return self._to_report(row)

    def list_reports(self, *, limit: int = 50) -> list[OpportunityReport]:
        rows = self.session.scalars(
            select(OpportunityReportRow)
            .order_by(OpportunityReportRow.created_at.desc())
            .limit(limit)
        )
        return [self._to_report(row) for row in rows]

    @staticmethod
    def _to_report(row: OpportunityReportRow) -> OpportunityReport:
        timestamps: dict = {}
        for key, value in (row.timestamps or {}).items():
            if value is None:
                timestamps[key] = None
            else:
                try:
                    timestamps[key] = datetime.fromisoformat(str(value))
                except ValueError:
                    timestamps[key] = None
        return OpportunityReport(
            id=row.id,
            collection_id=row.collection_id,
            query=row.query,
            title=row.title,
            summary=row.summary,
            problem=row.problem,
            audience=row.audience,
            geography=row.geography,
            language=row.language,
            demand_evidence=_parse_claims(row.demand_evidence),
            search_behaviour_keywords=list(row.search_behaviour_keywords or []),
            discussion_evidence=_parse_claims(row.discussion_evidence),
            competitors=list(row.competitors or []),
            competitor_weaknesses=_parse_claims(row.competitor_weaknesses),
            unmet_needs=_parse_claims(row.unmet_needs),
            recommended_format=(
                SolutionFormat(row.recommended_format)
                if row.recommended_format
                else None
            ),
            alternative_formats=[
                SolutionFormat(v) for v in (row.alternative_formats or [])
            ],
            scores=_parse_scores(row.scores),
            complexity=row.complexity,
            build_maintenance=row.build_maintenance,
            monetization_hypotheses=list(row.monetization_hypotheses or []),
            risks=_parse_claims(row.risks),
            source_urls=list(row.source_urls or []),
            timestamps=timestamps,
            limitations=list(row.limitations or []),
            contradictions=list(row.contradictions or []),
            missing_info=list(row.missing_info or []),
            cheapest_validation_experiment=row.cheapest_validation_experiment,
            next_actions=list(row.next_actions or []),
            claims=_parse_claims(row.claims),
            evidence_ids=_parse_uuids(row.evidence_ids),
            opportunity_ids=_parse_uuids(row.opportunity_ids),
            format_recommendation_id=row.format_recommendation_id,
            gap_report_id=row.gap_report_id,
            attributes=dict(row.attributes or {}),
            created_at=row.created_at,
        )
