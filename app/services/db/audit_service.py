from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.audit import AuditLog


def create_audit_event(
    db: Session,
    user_id: str,
    event: str,
    module: str,
    detail: str | None = None,
    resource_id: str | None = None,
    status: str = "success",
) -> AuditLog:
    audit = AuditLog(
        user_id=user_id,
        event=event,
        module=module,
        status=status,
        detail=detail,
        resource_id=resource_id,
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)
    return audit


def list_audit_events(db: Session, user_id: str, limit: int = 100) -> list[AuditLog]:
    statement = (
        select(AuditLog)
        .options(joinedload(AuditLog.user))
        .where(AuditLog.user_id == user_id)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    )
    return list(db.scalars(statement).all())
