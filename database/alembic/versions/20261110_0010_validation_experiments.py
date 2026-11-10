"""validation experiments

Revision ID: 20261110_0010
Revises: 20261110_0009
Create Date: 2026-11-10 19:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261110_0010"
down_revision: Union[str, Sequence[str], None] = "20261110_0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "validation_experiments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("report_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("collection_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("hypothesis", sa.Text(), nullable=False),
        sa.Column("experiment", sa.Text(), nullable=False),
        sa.Column("projected_cost_usd", sa.Float(), nullable=True),
        sa.Column("projected_time_days", sa.Float(), nullable=True),
        sa.Column(
            "success_criteria", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("measured_cost_usd", sa.Float(), nullable=True),
        sa.Column("measured_time_days", sa.Float(), nullable=True),
        sa.Column("results", sa.Text(), nullable=True),
        sa.Column("decision", sa.String(length=32), nullable=False),
        sa.Column("decision_rationale", sa.Text(), nullable=True),
        sa.Column("claims", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("missing_info", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("limitations", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("attributes", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_validation_experiments_report_id",
        "validation_experiments",
        ["report_id"],
    )
    op.create_index(
        "ix_validation_experiments_collection_id",
        "validation_experiments",
        ["collection_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_validation_experiments_collection_id",
        table_name="validation_experiments",
    )
    op.drop_index(
        "ix_validation_experiments_report_id",
        table_name="validation_experiments",
    )
    op.drop_table("validation_experiments")
