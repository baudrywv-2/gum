"""evidence collection members for dedupe-aware discovery

Revision ID: 20261110_0005
Revises: 20261110_0004
Create Date: 2026-11-10 17:30:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261110_0005"
down_revision: Union[str, Sequence[str], None] = "20261110_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "evidence_collection_members",
        sa.Column("collection_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("evidence_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("collection_id", "evidence_id"),
    )
    # Backfill links for existing rows that already store collection_id.
    op.execute(
        """
        INSERT INTO evidence_collection_members (collection_id, evidence_id)
        SELECT collection_id, id
        FROM evidence_records
        WHERE collection_id IS NOT NULL
        ON CONFLICT DO NOTHING
        """
    )


def downgrade() -> None:
    op.drop_table("evidence_collection_members")
