from sqlalchemy import JSON, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base_model import TimestampIdMixin


class Acta(TimestampIdMixin, Base):
    __tablename__ = "actas"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    transcription: Mapped[str] = mapped_column(Text, nullable=False)
    diarization: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    result: Mapped[str] = mapped_column(Text, nullable=False)
    tasks: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)

    user: Mapped["User"] = relationship(back_populates="actas")
