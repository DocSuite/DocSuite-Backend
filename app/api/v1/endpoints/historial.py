from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.schemas.acta import ActaRead
from app.schemas.analysis import AnalysisRead
from app.services.db.acta_service import list_actas_by_user
from app.services.db.analysis_service import list_analyses_by_user

router = APIRouter()


@router.get("/analyses", response_model=list[AnalysisRead])
def get_analysis_history(db: DbSession, current_user: CurrentUser) -> list[AnalysisRead]:
    return [AnalysisRead.model_validate(item) for item in list_analyses_by_user(db, current_user.id)]


@router.get("/actas", response_model=list[ActaRead])
def get_acta_history(db: DbSession, current_user: CurrentUser) -> list[ActaRead]:
    return [ActaRead.model_validate(item) for item in list_actas_by_user(db, current_user.id)]
