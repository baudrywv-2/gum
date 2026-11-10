"""Health response schema."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(description="ok | degraded")
    service: str
    version: str
    database: str = Field(description="connected | unreachable")
    timestamp: datetime
