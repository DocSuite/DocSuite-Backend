from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base_model import TimestampIdMixin


class AuditLog(TimestampIdMixin, Base):
    __tablename__ = "audit_logs"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    event: Mapped[str] = mapped_column(String(120), nullable=False)
    module: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="success", nullable=False)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    user: Mapped["User"] = relationship(back_populates="audit_logs")
