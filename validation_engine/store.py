"""Persist validation experiments and outcomes."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import ValidationExperimentRow
from packages.contracts.claim_tags import ClaimTag
from packages.contracts.opportunities import LabeledClaim
from packages.contracts.validation import (
    ExperimentStatus,
    OutcomeSummary,
    ValidationDecision,
    ValidationExperiment,
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


class ValidationStore:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, experiment: ValidationExperiment) -> ValidationExperiment:
        experiment_id = experiment.id or uuid.uuid4()
        now = _utcnow()
        row = ValidationExperimentRow(
            id=experiment_id,
            report_id=experiment.report_id,
            collection_id=experiment.collection_id,
            query=experiment.query,
            hypothesis=experiment.hypothesis,
            experiment=experiment.experiment,
            projected_cost_usd=experiment.projected_cost_usd,
            projected_time_days=experiment.projected_time_days,
            success_criteria=list(experiment.success_criteria),
            status=experiment.status.value,
            measured_cost_usd=experiment.measured_cost_usd,
            measured_time_days=experiment.measured_time_days,
            results=experiment.results,
            decision=experiment.decision.value,
            decision_rationale=experiment.decision_rationale,
            claims=[c.model_dump(mode="json") for c in experiment.claims],
            missing_info=list(experiment.missing_info),
            limitations=list(experiment.limitations),
            attributes=dict(experiment.attributes),
            created_at=now,
            updated_at=now,
        )
        self.session.add(row)
        self.session.flush()
        return experiment.model_copy(
            update={"id": experiment_id, "created_at": now, "updated_at": now}
        )

    def get(self, experiment_id: uuid.UUID) -> ValidationExperiment | None:
        row = self.session.get(ValidationExperimentRow, experiment_id)
        if row is None:
            return None
        return self._to_model(row)

    def list_experiments(self, *, limit: int = 50) -> list[ValidationExperiment]:
        rows = self.session.scalars(
            select(ValidationExperimentRow)
            .order_by(ValidationExperimentRow.created_at.desc())
            .limit(limit)
        )
        return [self._to_model(row) for row in rows]

    def list_outcomes(self, *, limit: int = 50) -> list[OutcomeSummary]:
        rows = self.session.scalars(
            select(ValidationExperimentRow)
            .where(ValidationExperimentRow.decision != ValidationDecision.PENDING.value)
            .order_by(ValidationExperimentRow.updated_at.desc())
            .limit(limit)
        )
        return [
            OutcomeSummary(
                experiment_id=row.id,
                query=row.query,
                hypothesis=row.hypothesis,
                decision=ValidationDecision(row.decision),
                projected_cost_usd=row.projected_cost_usd,
                measured_cost_usd=row.measured_cost_usd,
                projected_time_days=row.projected_time_days,
                measured_time_days=row.measured_time_days,
                results=row.results,
            )
            for row in rows
        ]

    def record_outcome(
        self,
        experiment_id: uuid.UUID,
        *,
        measured_cost_usd: float | None,
        measured_time_days: float | None,
        results: str,
        decision: ValidationDecision,
        decision_rationale: str | None,
        status: ExperimentStatus,
    ) -> ValidationExperiment:
        row = self.session.get(ValidationExperimentRow, experiment_id)
        if row is None:
            raise ValueError(f"Unknown experiment_id: {experiment_id}")
        if decision is ValidationDecision.PENDING:
            raise ValueError("Outcome decision must be continue, pivot, or abandon")
        row.measured_cost_usd = measured_cost_usd
        row.measured_time_days = measured_time_days
        row.results = results
        row.decision = decision.value
        row.decision_rationale = decision_rationale
        row.status = status.value
        row.updated_at = _utcnow()
        self.session.flush()
        return self._to_model(row)

    @staticmethod
    def _to_model(row: ValidationExperimentRow) -> ValidationExperiment:
        return ValidationExperiment(
            id=row.id,
            report_id=row.report_id,
            collection_id=row.collection_id,
            query=row.query,
            hypothesis=row.hypothesis,
            experiment=row.experiment,
            projected_cost_usd=row.projected_cost_usd,
            projected_time_days=row.projected_time_days,
            success_criteria=list(row.success_criteria or []),
            status=ExperimentStatus(row.status),
            measured_cost_usd=row.measured_cost_usd,
            measured_time_days=row.measured_time_days,
            results=row.results,
            decision=ValidationDecision(row.decision),
            decision_rationale=row.decision_rationale,
            claims=_parse_claims(row.claims),
            missing_info=list(row.missing_info or []),
            limitations=list(row.limitations or []),
            attributes=dict(row.attributes or {}),
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
