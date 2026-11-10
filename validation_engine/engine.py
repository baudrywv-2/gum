"""Validation engine orchestrator."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from format_engine.store import FormatStore
from packages.contracts.scoring import GenerateReportRequest
from packages.contracts.validation import (
    ProposeExperimentsRequest,
    ProposeExperimentsResult,
    RecordOutcomeRequest,
    ValidationExperiment,
)
from scoring_engine.report import ReportEngine
from scoring_engine.store import ScoringStore
from validation_engine.propose import propose_from_format, propose_from_report
from validation_engine.store import ValidationStore


class ValidationEngine:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.store = ValidationStore(session)
        self.scoring_store = ScoringStore(session)
        self.format_store = FormatStore(session)
        self.report_engine = ReportEngine(session)

    def propose(self, request: ProposeExperimentsRequest) -> ProposeExperimentsResult:
        limitations = [
            "Projected cost/time are hypotheses — keep separate from measured outcomes.",
            "Decisions require recorded results; never invent success.",
        ]
        experiments: list[ValidationExperiment] = []

        if request.report_id is not None:
            report = self.scoring_store.get_report(request.report_id)
            if report is None:
                raise ValueError(f"Unknown report_id: {request.report_id}")
            experiments = propose_from_report(
                report, max_experiments=request.max_experiments
            )
        else:
            generated = self.report_engine.generate(
                GenerateReportRequest(
                    query=request.query,
                    geography=request.geography,
                    language=request.language,
                    collection_id=request.collection_id,
                )
            )
            limitations.extend(generated.limitations)
            if generated.reports:
                experiments = propose_from_report(
                    generated.reports[0], max_experiments=request.max_experiments
                )
            else:
                # Fallback: newest format recommendation for query collection
                formats = self.format_store.list_recommendations(limit=1)
                if formats:
                    experiments = propose_from_format(
                        query=request.query,
                        format_rec=formats[0],
                        collection_id=formats[0].collection_id,
                        max_experiments=request.max_experiments,
                    )

        if not experiments:
            raise ValueError(
                "Could not propose experiments — generate a report first or pass report_id"
            )

        saved = [self.store.save(exp) for exp in experiments]
        self.session.commit()
        return ProposeExperimentsResult(
            experiments=saved,
            count=len(saved),
            limitations=list(dict.fromkeys(limitations)),
        )

    def record_outcome(
        self, experiment_id: UUID, request: RecordOutcomeRequest
    ) -> ValidationExperiment:
        updated = self.store.record_outcome(
            experiment_id,
            measured_cost_usd=request.measured_cost_usd,
            measured_time_days=request.measured_time_days,
            results=request.results,
            decision=request.decision,
            decision_rationale=request.decision_rationale,
            status=request.status,
        )
        self.session.commit()
        return updated
