from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.acta import Acta
from app.schemas.acta import ActaCreate


def create_acta(db: Session, user_id: str, payload: ActaCreate) -> Acta:
    data = payload.model_dump()
    data["tasks"] = [task.model_dump() if hasattr(task, "model_dump") else task for task in payload.tasks]
    acta = Acta(user_id=user_id, **data)
    db.add(acta)
    db.commit()
    db.refresh(acta)
    return acta


def list_actas_by_user(db: Session, user_id: str) -> list[Acta]:
    statement = select(Acta).where(Acta.user_id == user_id).order_by(Acta.created_at.desc())
    return list(db.scalars(statement).all())
