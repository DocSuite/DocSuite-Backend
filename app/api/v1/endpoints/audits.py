from fastapi import APIRouter, Query

from app.api.deps import AdminUser, DbSession
from app.schemas.audit import AuditRead
from app.services.db.audit_service import list_audit_events

router = APIRouter()


@router.get("", response_model=list[AuditRead])
def get_audit_events(
    db: DbSession,
    current_user: AdminUser,
    limit: int = Query(default=100, ge=1, le=200),
) -> list[AuditRead]:
    events = list_audit_events(db, limit=limit)
    return [
        AuditRead.model_validate(
            {
                **event.__dict__,
                "user_email": event.user.email,
            }
        )
        for event in events
    ]
