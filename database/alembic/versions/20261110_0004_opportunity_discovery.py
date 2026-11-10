"""opportunity runs, clusters, and opportunities

Revision ID: 20261110_0004
Revises: 20261110_0003
Create Date: 2026-11-10 17:25:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261110_0004"
down_revision: Union[str, Sequence[str], None] = "20261110_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "opportunity_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("collection_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("geography", sa.String(length=64), nullable=True),
        sa.Column("language", sa.String(length=32), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_opportunity_runs_collection_id", "opportunity_runs", ["collection_id"]
    )

    op.create_table(
        "evidence_clusters",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("label", sa.Text(), nullable=False),
        sa.Column("evidence_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("providers", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("kinds", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "shared_tokens", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column("size", sa.Integer(), nullable=False),
        sa.Column("claim_tag", sa.String(length=64), nullable=False),
        sa.Column("limitations", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_evidence_clusters_run_id", "evidence_clusters", ["run_id"])

    op.create_table(
        "opportunities",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("collection_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("opportunity_type", sa.String(length=64), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("problem", sa.Text(), nullable=False),
        sa.Column("audience", sa.Text(), nullable=True),
        sa.Column("geography", sa.String(length=64), nullable=True),
        sa.Column("language", sa.String(length=32), nullable=True),
        sa.Column("claims", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("evidence_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("providers", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("themes", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("missing_info", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("limitations", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("attributes", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_opportunities_run_id", "opportunities", ["run_id"])
    op.create_index("ix_opportunities_collection_id", "opportunities", ["collection_id"])
    op.create_index(
        "ix_opportunities_opportunity_type", "opportunities", ["opportunity_type"]
    )


def downgrade() -> None:
    op.drop_index("ix_opportunities_opportunity_type", table_name="opportunities")
    op.drop_index("ix_opportunities_collection_id", table_name="opportunities")
    op.drop_index("ix_opportunities_run_id", table_name="opportunities")
    op.drop_table("opportunities")
    op.drop_index("ix_evidence_clusters_run_id", table_name="evidence_clusters")
    op.drop_table("evidence_clusters")
    op.drop_index("ix_opportunity_runs_collection_id", table_name="opportunity_runs")
    op.drop_table("opportunity_runs")
