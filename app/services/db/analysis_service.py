from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.analysis import Analysis
from app.schemas.analysis import AnalysisCreate


def create_analysis(db: Session, user_id: str, payload: AnalysisCreate) -> Analysis:
    analysis = Analysis(user_id=user_id, **payload.model_dump())
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis


def list_analyses_by_user(db: Session, user_id: str) -> list[Analysis]:
    statement = select(Analysis).where(Analysis.user_id == user_id).order_by(Analysis.created_at.desc())
    return list(db.scalars(statement).all())
