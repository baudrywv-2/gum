"""evidence collections, records, and pain points

Revision ID: 20261110_0003
Revises: 20261110_0002
Create Date: 2026-11-10 17:20:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261110_0003"
down_revision: Union[str, Sequence[str], None] = "20261110_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "evidence_collections",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
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

    op.create_table(
        "evidence_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("collection_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("fingerprint", sa.String(length=64), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("provider_mode", sa.String(length=32), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("query", sa.Text(), nullable=True),
        sa.Column("geography", sa.String(length=64), nullable=True),
        sa.Column("language", sa.String(length=32), nullable=True),
        sa.Column("claim_tag", sa.String(length=64), nullable=False),
        sa.Column("reliability", sa.String(length=32), nullable=False),
        sa.Column("limitations", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("attributes", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("raw", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("fingerprint"),
    )
    op.create_index("ix_evidence_records_collection_id", "evidence_records", ["collection_id"])
    op.create_index("ix_evidence_records_kind", "evidence_records", ["kind"])
    op.create_index("ix_evidence_records_provider", "evidence_records", ["provider"])

    op.create_table(
        "pain_points",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("collection_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("normalized_text", sa.String(length=512), nullable=False),
        sa.Column("frequency", sa.Integer(), nullable=False),
        sa.Column("claim_tag", sa.String(length=64), nullable=False),
        sa.Column("evidence_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "source_providers", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column("limitations", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("normalized_text"),
    )
    op.create_index("ix_pain_points_collection_id", "pain_points", ["collection_id"])


def downgrade() -> None:
    op.drop_index("ix_pain_points_collection_id", table_name="pain_points")
    op.drop_table("pain_points")
    op.drop_index("ix_evidence_records_provider", table_name="evidence_records")
    op.drop_index("ix_evidence_records_kind", table_name="evidence_records")
    op.drop_index("ix_evidence_records_collection_id", table_name="evidence_records")
    op.drop_table("evidence_records")
    op.drop_table("evidence_collections")
