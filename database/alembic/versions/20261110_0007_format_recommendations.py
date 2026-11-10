"""format recommendations and evaluations

Revision ID: 20261110_0007
Revises: 20261110_0006
Create Date: 2026-11-10 17:45:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261110_0007"
down_revision: Union[str, Sequence[str], None] = "20261110_0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "format_recommendations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("collection_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("geography", sa.String(length=64), nullable=True),
        sa.Column("language", sa.String(length=32), nullable=True),
        sa.Column("primary_format", sa.String(length=64), nullable=False),
        sa.Column("alternatives", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("complementary", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("rejected", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("claims", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("missing_info", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("limitations", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_format_recommendations_collection_id",
        "format_recommendations",
        ["collection_id"],
    )

    op.create_table(
        "format_evaluations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("recommendation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("format", sa.String(length=64), nullable=False),
        sa.Column("decision", sa.String(length=32), nullable=False),
        sa.Column("fit_score", sa.Float(), nullable=False),
        sa.Column("complexity", sa.String(length=32), nullable=False),
        sa.Column("maintenance", sa.String(length=32), nullable=False),
        sa.Column(
            "monetization_hypotheses",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("cheapest_validation", sa.Text(), nullable=False),
        sa.Column(
            "reasons_selected", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column(
            "reasons_rejected", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column("evidence_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
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
    op.create_index(
        "ix_format_evaluations_recommendation_id",
        "format_evaluations",
        ["recommendation_id"],
    )
    op.create_index("ix_format_evaluations_format", "format_evaluations", ["format"])


def downgrade() -> None:
    op.drop_index("ix_format_evaluations_format", table_name="format_evaluations")
    op.drop_index(
        "ix_format_evaluations_recommendation_id", table_name="format_evaluations"
    )
    op.drop_table("format_evaluations")
    op.drop_index(
        "ix_format_recommendations_collection_id", table_name="format_recommendations"
    )
    op.drop_table("format_recommendations")
