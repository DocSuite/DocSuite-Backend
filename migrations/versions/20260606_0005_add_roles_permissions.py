"""add roles and permissions

Revision ID: 20260606_0005
Revises: 20260525_0004
Create Date: 2026-06-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260606_0005"
down_revision: str | None = "20260525_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("description", sa.String(length=250), nullable=True),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "app_views",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("route", sa.String(length=150), nullable=False),
        sa.Column("group", sa.String(length=80), nullable=True),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_table(
        "role_view_permissions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("view_id", sa.Integer(), nullable=False),
        sa.Column("can_read", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("can_create", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("can_update", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("can_delete", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"]),
        sa.ForeignKeyConstraint(["view_id"], ["app_views.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("role_id", "view_id", name="uq_role_view_permissions"),
    )

    roles = sa.table(
        "roles",
        sa.column("id", sa.Integer),
        sa.column("name", sa.String),
        sa.column("description", sa.String),
        sa.column("is_system", sa.Boolean),
    )
    app_views = sa.table(
        "app_views",
        sa.column("id", sa.Integer),
        sa.column("code", sa.String),
        sa.column("name", sa.String),
        sa.column("route", sa.String),
        sa.column("group", sa.String),
        sa.column("display_order", sa.Integer),
        sa.column("active", sa.Boolean),
    )
    role_view_permissions = sa.table(
        "role_view_permissions",
        sa.column("role_id", sa.Integer),
        sa.column("view_id", sa.Integer),
        sa.column("can_read", sa.Boolean),
        sa.column("can_create", sa.Boolean),
        sa.column("can_update", sa.Boolean),
        sa.column("can_delete", sa.Boolean),
    )

    op.bulk_insert(
        roles,
        [
            {
                "id": 1,
                "name": "admin",
                "description": "Administrador del sistema",
                "is_system": True,
            },
            {"id": 2, "name": "docente", "description": "Docente", "is_system": True},
            {"id": 3, "name": "estudiante", "description": "Estudiante", "is_system": True},
        ],
    )
    op.bulk_insert(
        app_views,
        [
            {
                "id": 1,
                "code": "dashboard",
                "name": "Dashboard",
                "route": "/dashboard",
                "group": "General",
                "display_order": 1,
                "active": True,
            },
            {
                "id": 2,
                "code": "profile",
                "name": "Perfil",
                "route": "/profile",
                "group": "General",
                "display_order": 2,
                "active": True,
            },
            {
                "id": 3,
                "code": "doc_acta",
                "name": "DocActa",
                "route": "/doc-acta",
                "group": "Documentos",
                "display_order": 3,
                "active": True,
            },
            {
                "id": 4,
                "code": "history",
                "name": "Historial",
                "route": "/history",
                "group": "Documentos",
                "display_order": 4,
                "active": True,
            },
            {
                "id": 5,
                "code": "audits",
                "name": "Auditorias",
                "route": "/audits",
                "group": "Admin",
                "display_order": 5,
                "active": True,
            },
            {
                "id": 6,
                "code": "admin_users",
                "name": "Usuarios",
                "route": "/admin/users",
                "group": "Admin",
                "display_order": 6,
                "active": True,
            },
            {
                "id": 7,
                "code": "admin_roles",
                "name": "Roles",
                "route": "/admin/roles",
                "group": "Admin",
                "display_order": 7,
                "active": True,
            },
            {
                "id": 8,
                "code": "admin_storage",
                "name": "Storage",
                "route": "/admin/storage",
                "group": "Admin",
                "display_order": 8,
                "active": True,
            },
            {
                "id": 9,
                "code": "doc_analyzer",
                "name": "DocAnalyzer",
                "route": "/doc-analyzer",
                "group": "Documentos",
                "display_order": 9,
                "active": True,
            },
        ],
    )
    op.bulk_insert(
        role_view_permissions,
        [
            {
                "role_id": 1,
                "view_id": 1,
                "can_read": True,
                "can_create": True,
                "can_update": True,
                "can_delete": True,
            },
            {
                "role_id": 1,
                "view_id": 2,
                "can_read": True,
                "can_create": True,
                "can_update": True,
                "can_delete": True,
            },
            {
                "role_id": 1,
                "view_id": 3,
                "can_read": True,
                "can_create": True,
                "can_update": True,
                "can_delete": True,
            },
            {
                "role_id": 1,
                "view_id": 4,
                "can_read": True,
                "can_create": True,
                "can_update": True,
                "can_delete": True,
            },
            {
                "role_id": 1,
                "view_id": 5,
                "can_read": True,
                "can_create": False,
                "can_update": False,
                "can_delete": False,
            },
            {
                "role_id": 1,
                "view_id": 6,
                "can_read": True,
                "can_create": True,
                "can_update": True,
                "can_delete": True,
            },
            {
                "role_id": 1,
                "view_id": 7,
                "can_read": True,
                "can_create": True,
                "can_update": True,
                "can_delete": True,
            },
            {
                "role_id": 1,
                "view_id": 8,
                "can_read": True,
                "can_create": True,
                "can_update": True,
                "can_delete": True,
            },
            {
                "role_id": 1,
                "view_id": 9,
                "can_read": True,
                "can_create": True,
                "can_update": True,
                "can_delete": True,
            },
            {
                "role_id": 2,
                "view_id": 1,
                "can_read": True,
                "can_create": False,
                "can_update": False,
                "can_delete": False,
            },
            {
                "role_id": 2,
                "view_id": 2,
                "can_read": True,
                "can_create": False,
                "can_update": True,
                "can_delete": False,
            },
            {
                "role_id": 2,
                "view_id": 3,
                "can_read": True,
                "can_create": True,
                "can_update": True,
                "can_delete": False,
            },
            {
                "role_id": 2,
                "view_id": 4,
                "can_read": True,
                "can_create": False,
                "can_update": False,
                "can_delete": False,
            },
            {
                "role_id": 2,
                "view_id": 9,
                "can_read": True,
                "can_create": True,
                "can_update": False,
                "can_delete": False,
            },
            {
                "role_id": 3,
                "view_id": 1,
                "can_read": True,
                "can_create": False,
                "can_update": False,
                "can_delete": False,
            },
            {
                "role_id": 3,
                "view_id": 2,
                "can_read": True,
                "can_create": False,
                "can_update": True,
                "can_delete": False,
            },
            {
                "role_id": 3,
                "view_id": 4,
                "can_read": True,
                "can_create": False,
                "can_update": False,
                "can_delete": False,
            },
        ],
    )

    op.add_column("users", sa.Column("role_id", sa.Integer(), nullable=True))
    op.execute("UPDATE users SET role_id = 2")
    op.execute("UPDATE users SET role_id = 1 WHERE email = 'admin@docsuite.edu.pe'")
    op.alter_column("users", "role_id", existing_type=sa.Integer(), nullable=False)
    op.create_foreign_key("fk_users_role_id_roles", "users", "roles", ["role_id"], ["id"])


def downgrade() -> None:
    op.drop_constraint("fk_users_role_id_roles", "users", type_="foreignkey")
    op.drop_column("users", "role_id")
    op.drop_table("role_view_permissions")
    op.drop_table("app_views")
    op.drop_table("roles")
