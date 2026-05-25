"""add acta_jobs table

Revision ID: 20260524_0002
Revises: 20260524_0001
Create Date: 2026-05-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260524_0002"
down_revision: str | None = "20260524_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "acta_jobs",
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=1024), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="queued"),
        sa.Column("progress", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("message", sa.String(length=500), nullable=False, server_default="En cola"),
        sa.Column("acta_id", sa.String(length=36), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["acta_id"], ["actas.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_acta_jobs_user_id", "acta_jobs", ["user_id"])
    op.create_index("ix_acta_jobs_status", "acta_jobs", ["status"])


def downgrade() -> None:
    op.drop_index("ix_acta_jobs_status", table_name="acta_jobs")
    op.drop_index("ix_acta_jobs_user_id", table_name="acta_jobs")
    op.drop_table("acta_jobs")
