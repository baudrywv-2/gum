"""Shared health contract mirrored by the API response."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class HealthStatus(BaseModel):
    status: str = Field(description="ok | degraded")
    service: str
    version: str
    database: str = Field(description="connected | unreachable")
    timestamp: datetime
