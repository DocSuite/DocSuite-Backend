from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base_model import TimestampIdMixin


class ActaJobRecord(TimestampIdMixin, Base):
    __tablename__ = "acta_jobs"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="queued", nullable=False)
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    message: Mapped[str] = mapped_column(String(500), default="En cola", nullable=False)
    acta_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("actas.id"), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
