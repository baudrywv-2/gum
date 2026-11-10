"""Health-check endpoints."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)) -> HealthResponse:
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:  # noqa: BLE001 — surface status, not stack traces
        db_ok = False

    status = "ok" if db_ok else "degraded"
    return HealthResponse(
        status=status,
        service="gum-api",
        version="0.6.0",
        database="connected" if db_ok else "unreachable",
        timestamp=datetime.now(timezone.utc),
    )
