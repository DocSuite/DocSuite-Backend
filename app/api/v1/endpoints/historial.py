from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import DbSession, require_permission
from app.models.user import User
from app.schemas.acta import ActaRead
from app.schemas.analysis import AnalysisRead
from app.services.db.acta_service import list_actas_by_user
from app.services.db.analysis_service import list_analyses_by_user

router = APIRouter()

HistoryReader = Annotated[User, Depends(require_permission("/history"))]
SearchQuery = Annotated[
    str | None,
    Query(default=None, description="Buscar en nombre de archivo, transcripcion y acta"),
]
FromDateQuery = Annotated[str | None, Query(description="Fecha inicio (YYYY-MM-DD)")]
ToDateQuery = Annotated[str | None, Query(description="Fecha fin (YYYY-MM-DD)")]


@router.get("/document-analyses", response_model=list[AnalysisRead])
def get_analysis_history(
    db: DbSession,
    current_user: HistoryReader,
) -> list[AnalysisRead]:
    return [
        AnalysisRead.model_validate(item) for item in list_analyses_by_user(db, current_user.id)
    ]


@router.get("/meeting-minutes", response_model=list[ActaRead])
def get_acta_history(
    db: DbSession,
    current_user: HistoryReader,
    q: str | None = Query(
        default=None, description="Buscar en nombre de archivo, transcripción y acta"
    ),
    from_date: FromDateQuery = None,
    to_date: ToDateQuery = None,
) -> list[ActaRead]:
    items = list_actas_by_user(db, current_user.id, q=q, from_date=from_date, to_date=to_date)
    return [ActaRead.model_validate(item) for item in items]
