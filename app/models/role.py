from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(250), nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    users: Mapped[list["User"]] = relationship(back_populates="role")
    permissions: Mapped[list["RoleViewPermission"]] = relationship(
        back_populates="role",
        cascade="all, delete-orphan",
    )


class AppView(Base):
    __tablename__ = "app_views"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    route: Mapped[str] = mapped_column(String(150), nullable=False)
    group: Mapped[str | None] = mapped_column(String(80), nullable=True)
    order: Mapped[int] = mapped_column("display_order", Integer, default=0, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    permissions: Mapped[list["RoleViewPermission"]] = relationship(
        back_populates="view",
        cascade="all, delete-orphan",
    )


class RoleViewPermission(Base):
    __tablename__ = "role_view_permissions"
    __table_args__ = (UniqueConstraint("role_id", "view_id", name="uq_role_view_permissions"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False)
    view_id: Mapped[int] = mapped_column(ForeignKey("app_views.id"), nullable=False)
    can_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    can_create: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    can_update: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    can_delete: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    role: Mapped[Role] = relationship(back_populates="permissions")
    view: Mapped[AppView] = relationship(back_populates="permissions")
