"""Validation experiment API (Milestone 10)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.validation import (
    ExperimentListResponse,
    OutcomeListResponse,
    ProposeExperimentsBody,
    ProposeExperimentsResponse,
    RecordOutcomeBody,
)
from packages.contracts.validation import ValidationExperiment
from validation_engine.engine import ValidationEngine
from validation_engine.store import ValidationStore

router = APIRouter(prefix="/validation", tags=["validation"])


@router.post("/propose", response_model=ProposeExperimentsResponse)
def propose_experiments(
    body: ProposeExperimentsBody, db: Session = Depends(get_db)
) -> ProposeExperimentsResponse:
    engine = ValidationEngine(db)
    try:
        result = engine.propose(body)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ProposeExperimentsResponse.model_validate(result.model_dump())


@router.get("/experiments", response_model=ExperimentListResponse)
def list_experiments(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> ExperimentListResponse:
    rows = ValidationStore(db).list_experiments(limit=limit)
    return ExperimentListResponse(experiments=rows, count=len(rows))


@router.get("/experiments/{experiment_id}", response_model=ValidationExperiment)
def get_experiment(
    experiment_id: UUID, db: Session = Depends(get_db)
) -> ValidationExperiment:
    row = ValidationStore(db).get(experiment_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return row


@router.post(
    "/experiments/{experiment_id}/outcome",
    response_model=ValidationExperiment,
)
def record_outcome(
    experiment_id: UUID,
    body: RecordOutcomeBody,
    db: Session = Depends(get_db),
) -> ValidationExperiment:
    engine = ValidationEngine(db)
    try:
        return engine.record_outcome(experiment_id, body)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/outcomes", response_model=OutcomeListResponse)
def list_outcomes(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> OutcomeListResponse:
    rows = ValidationStore(db).list_outcomes(limit=limit)
    return OutcomeListResponse(outcomes=rows, count=len(rows))
