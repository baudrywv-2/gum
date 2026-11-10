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


class EvidenceCollectionMember(Base):
    """Many-to-many link so deduped evidence stays visible on later collections."""

    __tablename__ = "evidence_collection_members"

    collection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True
    )
    evidence_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True
    )
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


class OpportunityRun(Base):
    """One opportunity-discovery run over an evidence collection."""

    __tablename__ = "opportunity_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    collection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    query: Mapped[str] = mapped_column(Text, nullable=False)
    geography: Mapped[str | None] = mapped_column(String(64), nullable=True)
    language: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="completed")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class EvidenceClusterRow(Base):
    """Persisted evidence clusters from a discovery run."""

    __tablename__ = "evidence_clusters"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    label: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_ids: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    providers: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    kinds: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    shared_tokens: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    claim_tag: Mapped[str] = mapped_column(String(64), nullable=False)
    limitations: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class OpportunityRow(Base):
    """Discovered opportunity candidate with labeled claims."""

    __tablename__ = "opportunities"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    collection_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    opportunity_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    problem: Mapped[str] = mapped_column(Text, nullable=False)
    audience: Mapped[str | None] = mapped_column(Text, nullable=True)
    geography: Mapped[str | None] = mapped_column(String(64), nullable=True)
    language: Mapped[str | None] = mapped_column(String(32), nullable=True)
    claims: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    evidence_ids: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    providers: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    themes: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    missing_info: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    limitations: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    attributes: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class GapReportRow(Base):
    """Persisted competitor/gap analysis report."""

    __tablename__ = "gap_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    collection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    query: Mapped[str] = mapped_column(Text, nullable=False)
    geography: Mapped[str | None] = mapped_column(String(64), nullable=True)
    language: Mapped[str | None] = mapped_column(String(32), nullable=True)
    search_vs_feedback: Mapped[str] = mapped_column(Text, nullable=False)
    claims: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    missing_info: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    limitations: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class CompetitorRow(Base):
    """Competitor / existing-solution profile tied to a gap report."""

    __tablename__ = "competitors"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_providers: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    search_evidence_ids: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    feedback_evidence_ids: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    claims: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    weaknesses: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    limitations: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    attributes: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class GapFindingRow(Base):
    """Individual evidence-backed gap finding."""

    __tablename__ = "gap_findings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    kind: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    claims: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    evidence_ids: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    competitor_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    missing_info: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    limitations: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    attributes: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class FormatRecommendationRow(Base):
    """Persisted solution-format recommendation."""

    __tablename__ = "format_recommendations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    collection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    query: Mapped[str] = mapped_column(Text, nullable=False)
    geography: Mapped[str | None] = mapped_column(String(64), nullable=True)
    language: Mapped[str | None] = mapped_column(String(32), nullable=True)
    primary_format: Mapped[str] = mapped_column(String(64), nullable=False)
    alternatives: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    complementary: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    rejected: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    claims: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    missing_info: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    limitations: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class FormatEvaluationRow(Base):
    """Per-format evaluation with select/reject reasons."""

    __tablename__ = "format_evaluations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    recommendation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    format: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    decision: Mapped[str] = mapped_column(String(32), nullable=False)
    fit_score: Mapped[float] = mapped_column(Float, nullable=False)
    complexity: Mapped[str] = mapped_column(String(32), nullable=False)
    maintenance: Mapped[str] = mapped_column(String(32), nullable=False)
    monetization_hypotheses: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    cheapest_validation: Mapped[str] = mapped_column(Text, nullable=False)
    reasons_selected: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    reasons_rejected: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    evidence_ids: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    missing_info: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    limitations: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    attributes: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class OpportunityReportRow(Base):
    """Persisted structured opportunity report with scores (Milestone 7)."""

    __tablename__ = "opportunity_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    collection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    query: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    problem: Mapped[str] = mapped_column(Text, nullable=False)
    audience: Mapped[str | None] = mapped_column(Text, nullable=True)
    geography: Mapped[str | None] = mapped_column(String(64), nullable=True)
    language: Mapped[str | None] = mapped_column(String(32), nullable=True)
    demand_evidence: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    search_behaviour_keywords: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    discussion_evidence: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    competitors: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    competitor_weaknesses: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    unmet_needs: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    recommended_format: Mapped[str | None] = mapped_column(String(64), nullable=True)
    alternative_formats: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    scores: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    complexity: Mapped[str | None] = mapped_column(String(32), nullable=True)
    build_maintenance: Mapped[str | None] = mapped_column(Text, nullable=True)
    monetization_hypotheses: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    risks: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    source_urls: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    timestamps: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    limitations: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    contradictions: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    missing_info: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    cheapest_validation_experiment: Mapped[str | None] = mapped_column(Text, nullable=True)
    next_actions: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    claims: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    evidence_ids: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    opportunity_ids: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    format_recommendation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    gap_report_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    attributes: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class SavedOpportunityRow(Base):
    """Bookmarked opportunity report (MCP / dashboard save)."""

    __tablename__ = "saved_opportunities"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    query: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    attributes: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ValidationExperimentRow(Base):
    """Validation experiment with projected vs measured fields (Milestone 10)."""

    __tablename__ = "validation_experiments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    report_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    collection_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    query: Mapped[str] = mapped_column(Text, nullable=False)
    hypothesis: Mapped[str] = mapped_column(Text, nullable=False)
    experiment: Mapped[str] = mapped_column(Text, nullable=False)
    projected_cost_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    projected_time_days: Mapped[float | None] = mapped_column(Float, nullable=True)
    success_criteria: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="proposed")
    measured_cost_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    measured_time_days: Mapped[float | None] = mapped_column(Float, nullable=True)
    results: Mapped[str | None] = mapped_column(Text, nullable=True)
    decision: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    decision_rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    claims: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    missing_info: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    limitations: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    attributes: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
