"""API schemas for validation experiments."""

from __future__ import annotations

from pydantic import BaseModel

from packages.contracts.validation import (
    OutcomeSummary,
    ProposeExperimentsRequest,
    ProposeExperimentsResult,
    RecordOutcomeRequest,
    ValidationExperiment,
)


class ProposeExperimentsBody(ProposeExperimentsRequest):
    pass


class ProposeExperimentsResponse(ProposeExperimentsResult):
    pass


class RecordOutcomeBody(RecordOutcomeRequest):
    pass


class ExperimentListResponse(BaseModel):
    experiments: list[ValidationExperiment]
    count: int


class OutcomeListResponse(BaseModel):
    outcomes: list[OutcomeSummary]
    count: int
