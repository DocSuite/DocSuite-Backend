"""add duration_seconds to actas

Revision ID: 20260524_0003
Revises: 20260524_0002
Create Date: 2026-05-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260524_0003"
down_revision: str | None = "20260524_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("actas", sa.Column("duration_seconds", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("actas", "duration_seconds")
