"""add user dni

Revision ID: 20260606_0006
Revises: 20260606_0005
Create Date: 2026-06-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260606_0006"
down_revision: str | None = "20260606_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("dni", sa.String(length=8), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "dni")
