"""Persist format recommendations."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import FormatEvaluationRow, FormatRecommendationRow
from packages.contracts.claim_tags import ClaimTag
from packages.contracts.formats import (
    ComplexityLevel,
    FormatDecision,
    FormatEvaluation,
    FormatRecommendation,
    SolutionFormat,
)
from packages.contracts.opportunities import LabeledClaim


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _parse_claims(raw_claims: list) -> list[LabeledClaim]:
    claims: list[LabeledClaim] = []
    for raw in raw_claims or []:
        try:
            evidence_ids = []
            for eid in raw.get("evidence_ids") or []:
                try:
                    evidence_ids.append(uuid.UUID(str(eid)))
                except ValueError:
                    continue
            claims.append(
                LabeledClaim(
                    text=raw["text"],
                    claim_tag=ClaimTag(raw["claim_tag"]),
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


class FormatStore:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save_recommendation(
        self, recommendation: FormatRecommendation
    ) -> FormatRecommendation:
        rec_id = recommendation.id or uuid.uuid4()
        row = FormatRecommendationRow(
            id=rec_id,
            collection_id=recommendation.collection_id,
            query=recommendation.query,
            geography=recommendation.geography,
            language=recommendation.language,
            primary_format=recommendation.primary_format.value,
            alternatives=[f.value for f in recommendation.alternatives],
            complementary=[f.value for f in recommendation.complementary],
            rejected=[f.value for f in recommendation.rejected],
            summary=recommendation.summary,
            claims=[c.model_dump(mode="json") for c in recommendation.claims],
            missing_info=list(recommendation.missing_info),
            limitations=list(recommendation.limitations),
            created_at=_utcnow(),
        )
        self.session.add(row)
        self.session.flush()

        evaluations: list[FormatEvaluation] = []
        for evaluation in recommendation.evaluations:
            evaluations.append(self._save_evaluation(rec_id, evaluation))

        return recommendation.model_copy(
            update={
                "id": rec_id,
                "evaluations": evaluations,
                "created_at": row.created_at,
            }
        )

    def _save_evaluation(
        self, recommendation_id: uuid.UUID, evaluation: FormatEvaluation
    ) -> FormatEvaluation:
        row = FormatEvaluationRow(
            id=uuid.uuid4(),
            recommendation_id=recommendation_id,
            format=evaluation.format.value,
            decision=evaluation.decision.value,
            fit_score=evaluation.fit_score,
            complexity=evaluation.complexity.value,
            maintenance=evaluation.maintenance.value,
            monetization_hypotheses=list(evaluation.monetization_hypotheses),
            cheapest_validation=evaluation.cheapest_validation,
            reasons_selected=[c.model_dump(mode="json") for c in evaluation.reasons_selected],
            reasons_rejected=[c.model_dump(mode="json") for c in evaluation.reasons_rejected],
            evidence_ids=[str(i) for i in evaluation.evidence_ids],
            missing_info=list(evaluation.missing_info),
            limitations=list(evaluation.limitations),
            attributes=dict(evaluation.attributes),
            created_at=_utcnow(),
        )
        self.session.add(row)
        self.session.flush()
        return evaluation

    def get_recommendation(self, recommendation_id: uuid.UUID) -> FormatRecommendation | None:
        row = self.session.get(FormatRecommendationRow, recommendation_id)
        if row is None:
            return None
        evaluations = [
            self._to_evaluation(e)
            for e in self.session.scalars(
                select(FormatEvaluationRow).where(
                    FormatEvaluationRow.recommendation_id == recommendation_id
                )
            )
        ]
        return FormatRecommendation(
            id=row.id,
            collection_id=row.collection_id,
            query=row.query,
            geography=row.geography,
            language=row.language,
            primary_format=SolutionFormat(row.primary_format),
            alternatives=[SolutionFormat(v) for v in (row.alternatives or [])],
            complementary=[SolutionFormat(v) for v in (row.complementary or [])],
            rejected=[SolutionFormat(v) for v in (row.rejected or [])],
            evaluations=evaluations,
            summary=row.summary,
            claims=_parse_claims(row.claims),
            missing_info=list(row.missing_info or []),
            limitations=list(row.limitations or []),
            created_at=row.created_at,
        )

    def list_recommendations(self, *, limit: int = 50) -> list[FormatRecommendation]:
        rows = self.session.scalars(
            select(FormatRecommendationRow)
            .order_by(FormatRecommendationRow.created_at.desc())
            .limit(limit)
        )
        return [r for rid in rows if (r := self.get_recommendation(rid.id)) is not None]

    @staticmethod
    def _to_evaluation(row: FormatEvaluationRow) -> FormatEvaluation:
        return FormatEvaluation(
            format=SolutionFormat(row.format),
            decision=FormatDecision(row.decision),
            fit_score=float(row.fit_score),
            complexity=ComplexityLevel(row.complexity),
            maintenance=ComplexityLevel(row.maintenance),
            monetization_hypotheses=list(row.monetization_hypotheses or []),
            cheapest_validation=row.cheapest_validation,
            reasons_selected=_parse_claims(row.reasons_selected),
            reasons_rejected=_parse_claims(row.reasons_rejected),
            evidence_ids=_parse_uuids(row.evidence_ids),
            missing_info=list(row.missing_info or []),
            limitations=list(row.limitations or []),
            attributes=dict(row.attributes or {}),
        )
