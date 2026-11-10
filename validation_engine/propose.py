"""Propose cheapest validation experiments from scored reports / formats.

Projected values are hypotheses. Measured outcomes are recorded separately.
"""

from __future__ import annotations

from packages.contracts.claim_tags import ClaimTag
from packages.contracts.formats import FormatRecommendation
from packages.contracts.opportunities import LabeledClaim
from packages.contracts.scoring import OpportunityReport
from packages.contracts.validation import (
    ExperimentStatus,
    ValidationDecision,
    ValidationExperiment,
)


def propose_from_report(
    report: OpportunityReport,
    *,
    max_experiments: int = 3,
) -> list[ValidationExperiment]:
    experiments: list[ValidationExperiment] = []
    cheapest = report.cheapest_validation_experiment
    if cheapest:
        experiments.append(
            ValidationExperiment(
                report_id=report.id,
                collection_id=report.collection_id,
                query=report.query,
                hypothesis=(
                    f"If we validate via a cheap experiment for "
                    f"{report.recommended_format.value if report.recommended_format else 'the opportunity'}, "
                    f"we will learn whether demand is real enough to continue."
                ),
                experiment=cheapest,
                projected_cost_usd=50.0,
                projected_time_days=7.0,
                success_criteria=[
                    "At least one measured signal of intent (sign-up, reply, or paid interest)",
                    "No contradiction that the problem is fabricated",
                ],
                status=ExperimentStatus.PROPOSED,
                decision=ValidationDecision.PENDING,
                claims=[
                    LabeledClaim(
                        text="Cheapest validation copied from scored report (hypothesis).",
                        claim_tag=ClaimTag.HYPOTHESIS,
                        evidence_ids=list(report.evidence_ids)[:10],
                    )
                ],
                missing_info=["Measured conversion", "Actual spend"],
                limitations=[
                    "Projected cost/time are planning hypotheses, not quotes.",
                    "Success criteria must be filled with measured results later.",
                ],
                attributes={"source": "report.cheapest_validation_experiment"},
            )
        )

    for fmt in report.alternative_formats[: max(0, max_experiments - 1)]:
        experiments.append(
            ValidationExperiment(
                report_id=report.id,
                collection_id=report.collection_id,
                query=report.query,
                hypothesis=(
                    f"An alternative format ({fmt.value}) may validate cheaper or faster "
                    f"than the primary recommendation."
                ),
                experiment=(
                    f"Run a lightweight smoke test for format={fmt.value} "
                    f"(landing page, waitlist, or manual concierge) and record measured interest."
                ),
                projected_cost_usd=75.0,
                projected_time_days=10.0,
                success_criteria=[
                    "Measured interest exceeds a pre-declared threshold you set",
                    "Document why primary format was or was not beaten",
                ],
                status=ExperimentStatus.PROPOSED,
                decision=ValidationDecision.PENDING,
                claims=[
                    LabeledClaim(
                        text=f"Alternative format {fmt.value} proposed for validation (hypothesis).",
                        claim_tag=ClaimTag.HYPOTHESIS,
                        evidence_ids=list(report.evidence_ids)[:10],
                    )
                ],
                missing_info=["Pre-declared success threshold"],
                limitations=["Projected figures are not measured."],
                attributes={"source": "report.alternative_formats", "format": fmt.value},
            )
        )

    if not experiments:
        experiments.append(
            ValidationExperiment(
                report_id=report.id,
                collection_id=report.collection_id,
                query=report.query,
                hypothesis="Talking to 5 people with the stated problem will confirm or kill the opportunity.",
                experiment="Schedule 5 problem interviews; log verbatim quotes with claim tags.",
                projected_cost_usd=0.0,
                projected_time_days=5.0,
                success_criteria=[
                    "≥3 interviewees describe the same unmet need unprompted",
                ],
                status=ExperimentStatus.PROPOSED,
                decision=ValidationDecision.PENDING,
                claims=[
                    LabeledClaim(
                        text="Fallback interview experiment when no format validation text exists.",
                        claim_tag=ClaimTag.HYPOTHESIS,
                        evidence_ids=[],
                    )
                ],
                missing_info=["Interviewee list"],
                limitations=["No demand fabricated; interviews are qualitative."],
                attributes={"source": "fallback"},
            )
        )

    return experiments[:max_experiments]


def propose_from_format(
    *,
    query: str,
    format_rec: FormatRecommendation,
    report_id=None,
    collection_id=None,
    max_experiments: int = 3,
) -> list[ValidationExperiment]:
    primary = next(
        (e for e in format_rec.evaluations if e.format is format_rec.primary_format),
        None,
    )
    experiments: list[ValidationExperiment] = []
    if primary:
        experiments.append(
            ValidationExperiment(
                report_id=report_id,
                collection_id=collection_id or format_rec.collection_id,
                query=query,
                hypothesis=(
                    f"Primary format {primary.format.value} can be validated before heavy build."
                ),
                experiment=primary.cheapest_validation,
                projected_cost_usd=40.0,
                projected_time_days=5.0,
                success_criteria=[
                    "Complete the cheapest validation path and record measured outcome",
                ],
                status=ExperimentStatus.PROPOSED,
                decision=ValidationDecision.PENDING,
                claims=list(primary.reasons_selected)[:3]
                or [
                    LabeledClaim(
                        text="Derived from format recommender cheapest_validation.",
                        claim_tag=ClaimTag.HYPOTHESIS,
                        evidence_ids=list(primary.evidence_ids)[:10],
                    )
                ],
                missing_info=["Measured results"],
                limitations=["Projected cost/time are hypotheses."],
                attributes={"format": primary.format.value},
            )
        )
    return experiments[:max_experiments]
