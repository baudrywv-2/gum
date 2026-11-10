"""opportunity reports with scores

Revision ID: 20261110_0008
Revises: 20261110_0007
Create Date: 2026-11-10 18:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261110_0008"
down_revision: Union[str, Sequence[str], None] = "20261110_0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "opportunity_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("collection_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("problem", sa.Text(), nullable=False),
        sa.Column("audience", sa.Text(), nullable=True),
        sa.Column("geography", sa.String(length=64), nullable=True),
        sa.Column("language", sa.String(length=32), nullable=True),
        sa.Column("demand_evidence", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "search_behaviour_keywords",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "discussion_evidence", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column("competitors", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "competitor_weaknesses",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("unmet_needs", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("recommended_format", sa.String(length=64), nullable=True),
        sa.Column(
            "alternative_formats", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column("scores", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("complexity", sa.String(length=32), nullable=True),
        sa.Column("build_maintenance", sa.Text(), nullable=True),
        sa.Column(
            "monetization_hypotheses",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("risks", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("source_urls", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("timestamps", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("limitations", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("contradictions", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("missing_info", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("cheapest_validation_experiment", sa.Text(), nullable=True),
        sa.Column("next_actions", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("claims", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("evidence_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("opportunity_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("format_recommendation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("gap_report_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("attributes", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_opportunity_reports_collection_id",
        "opportunity_reports",
        ["collection_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_opportunity_reports_collection_id", table_name="opportunity_reports"
    )
    op.drop_table("opportunity_reports")
