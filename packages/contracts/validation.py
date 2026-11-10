"""Validation experiment and learning contracts (Milestone 10)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from packages.contracts.opportunities import LabeledClaim


class ValidationDecision(str, Enum):
    CONTINUE = "continue"
    PIVOT = "pivot"
    ABANDON = "abandon"
    PENDING = "pending"


class ExperimentStatus(str, Enum):
    PROPOSED = "proposed"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ValidationExperiment(BaseModel):
    id: UUID | None = None
    report_id: UUID | None = None
    collection_id: UUID | None = None
    query: str
    hypothesis: str
    experiment: str
    projected_cost_usd: float | None = None
    projected_time_days: float | None = None
    success_criteria: list[str] = Field(default_factory=list)
    status: ExperimentStatus = ExperimentStatus.PROPOSED
    measured_cost_usd: float | None = None
    measured_time_days: float | None = None
    results: str | None = None
    decision: ValidationDecision = ValidationDecision.PENDING
    decision_rationale: str | None = None
    claims: list[LabeledClaim] = Field(default_factory=list)
    missing_info: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    attributes: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ProposeExperimentsRequest(BaseModel):
    query: str = Field(min_length=1)
    report_id: UUID | None = None
    collection_id: UUID | None = None
    geography: str | None = None
    language: str | None = None
    max_experiments: int = Field(default=3, ge=1, le=10)


class ProposeExperimentsResult(BaseModel):
    experiments: list[ValidationExperiment] = Field(default_factory=list)
    count: int
    limitations: list[str] = Field(default_factory=list)


class RecordOutcomeRequest(BaseModel):
    measured_cost_usd: float | None = None
    measured_time_days: float | None = None
    results: str = Field(min_length=1)
    decision: ValidationDecision
    decision_rationale: str | None = None
    status: ExperimentStatus = ExperimentStatus.COMPLETED


class OutcomeSummary(BaseModel):
    experiment_id: UUID
    query: str
    hypothesis: str
    decision: ValidationDecision
    projected_cost_usd: float | None = None
    measured_cost_usd: float | None = None
    projected_time_days: float | None = None
    measured_time_days: float | None = None
    results: str | None = None
