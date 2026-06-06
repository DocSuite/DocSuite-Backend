from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import DbSession, require_permission
from app.models.user import User
from app.schemas.dashboard import DashboardRead
from app.services.db.dashboard_service import get_dashboard_summary

router = APIRouter()
DashboardReader = Annotated[User, Depends(require_permission("/dashboard"))]


@router.get("", response_model=DashboardRead)
def get_dashboard(db: DbSession, current_user: DashboardReader) -> DashboardRead:
    return get_dashboard_summary(db, current_user)
