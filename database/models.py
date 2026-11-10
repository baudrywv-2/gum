"""SQLAlchemy ORM models for GUM (foundation, providers, evidence)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class HealthProbe(Base):
    """Minimal table used to prove migrations apply."""

    __tablename__ = "health_probes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    label: Mapped[str] = mapped_column(String(128), nullable=False, default="foundation")
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ProviderUsageEvent(Base):
    """Persisted provider call / cost accounting rows."""

    __tablename__ = "provider_usage_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    provider: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    operation: Mapped[str] = mapped_column(String(64), nullable=False)
    mode: Mapped[str] = mapped_column(String(32), nullable=False)
    units: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    estimated_cost_usd: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    cached: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    query: Mapped[str | None] = mapped_column(Text, nullable=True)
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ProviderCacheEntry(Base):
    """Optional durable cache entries (in-memory cache remains primary in M2)."""

    __tablename__ = "provider_cache_entries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    cache_key: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    provider: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class EvidenceCollection(Base):
    """One evidence-collection run for a query."""

    __tablename__ = "evidence_collections"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    query: Mapped[str] = mapped_column(Text, nullable=False)
    geography: Mapped[str | None] = mapped_column(String(64), nullable=True)
    language: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="completed")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class EvidenceRecordRow(Base):
    """Persisted search or discussion evidence with provenance + fingerprint."""

    __tablename__ = "evidence_records"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    collection_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    kind: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    provider: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    provider_mode: Mapped[str] = mapped_column(String(32), nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    query: Mapped[str | None] = mapped_column(Text, nullable=True)
    geography: Mapped[str | None] = mapped_column(String(64), nullable=True)
    language: Mapped[str | None] = mapped_column(String(32), nullable=True)
    claim_tag: Mapped[str] = mapped_column(String(64), nullable=False)
    reliability: Mapped[str] = mapped_column(String(32), nullable=False, default="low")
    limitations: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    attributes: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    raw: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class PainPointRow(Base):
    """Recurring pain points extracted from discussion evidence."""

    __tablename__ = "pain_points"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    collection_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_text: Mapped[str] = mapped_column(String(512), nullable=False, unique=True)
    frequency: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    claim_tag: Mapped[str] = mapped_column(String(64), nullable=False)
    evidence_ids: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    source_providers: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    limitations: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
