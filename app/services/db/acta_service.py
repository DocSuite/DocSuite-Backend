from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.acta import Acta
from app.schemas.acta import ActaCreate, ActaUpdate


def create_acta(db: Session, user_id: str, payload: ActaCreate) -> Acta:
    data = payload.model_dump()
    data["tasks"] = [task.model_dump() if hasattr(task, "model_dump") else task for task in payload.tasks]
    acta = Acta(user_id=user_id, **data)
    db.add(acta)
    db.commit()
    db.refresh(acta)
    return acta


def get_acta_by_id(db: Session, acta_id: str, user_id: str) -> Acta | None:
    statement = select(Acta).where(Acta.id == acta_id, Acta.user_id == user_id)
    return db.scalars(statement).first()


def update_speaker_names(db: Session, acta: Acta, names: dict[str, str]) -> Acta:
    if acta.diarization is None:
        return acta

    updated_segments = []
    for segment in acta.diarization.get("segments", []):
        original = segment.get("speaker", "")
        updated_segments.append({**segment, "speaker": names.get(original, original)})

    updated_transcription = acta.transcription
    for original, real_name in names.items():
        updated_transcription = updated_transcription.replace(original, real_name)

    acta.diarization = {"segments": updated_segments}
    acta.transcription = updated_transcription
    db.commit()
    db.refresh(acta)
    return acta


def update_acta_content(db: Session, acta: Acta, payload: ActaUpdate) -> Acta:
    if payload.result is not None:
        acta.result = payload.result
    if payload.tasks is not None:
        acta.tasks = [t.model_dump() for t in payload.tasks]
    db.commit()
    db.refresh(acta)
    return acta


def list_actas_by_user(
    db: Session,
    user_id: str,
    q: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
) -> list[Acta]:
    stmt = select(Acta).where(Acta.user_id == user_id)

    if q:
        term = f"%{q}%"
        stmt = stmt.where(
            Acta.filename.ilike(term) | Acta.transcription.ilike(term) | Acta.result.ilike(term)
        )

    if from_date:
        stmt = stmt.where(Acta.created_at >= from_date)

    if to_date:
        stmt = stmt.where(Acta.created_at <= to_date)

    stmt = stmt.order_by(Acta.created_at.desc())
    return list(db.scalars(stmt).all())
