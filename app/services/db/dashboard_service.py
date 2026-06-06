from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.acta import Acta
from app.models.analysis import Analysis
from app.models.audit import AuditLog
from app.models.user import User
from app.schemas.dashboard import (
    DashboardActivityItem,
    DashboardAuditItem,
    DashboardDistributionItem,
    DashboardMetric,
    DashboardRead,
    DashboardTaskStatus,
    DashboardTrendPoint,
)
from app.services.db.role_service import ADMIN_ROLE_NAME
from app.utils.acta_tasks import extract_tasks_from_markdown


def get_dashboard_summary(db: Session, user: User) -> DashboardRead:
    user_id = None if user.role and user.role.name == ADMIN_ROLE_NAME else user.id
    analyses = _list_records(db, Analysis, user_id)
    actas = _list_records(db, Acta, user_id)
    audits = _list_audits(db, None if user_id is None else user.id)
    week_start = datetime.now(UTC) - timedelta(days=7)
    total_tasks, completed_tasks = _count_tasks(actas)

    return DashboardRead(
        metrics=[
            DashboardMetric(
                key="analyses",
                label="Documentos analizados",
                value=len(analyses),
                detail=f"{_count_since(analyses, week_start)} esta semana",
            ),
            DashboardMetric(
                key="actas",
                label="Actas generadas",
                value=len(actas),
                detail=f"{_count_since(actas, week_start)} esta semana",
            ),
            DashboardMetric(
                key="tasks",
                label="Tareas pendientes",
                value=total_tasks - completed_tasks,
                detail=f"{completed_tasks} completadas",
            ),
        ],
        trend=_build_trend(analyses, actas),
        distribution=[
            DashboardDistributionItem(label="Documentos", value=len(analyses)),
            DashboardDistributionItem(label="Actas", value=len(actas)),
        ],
        tasks=DashboardTaskStatus(pending=total_tasks - completed_tasks, completed=completed_tasks),
        activity=_build_activity(analyses, actas),
        audits=[
            DashboardAuditItem(
                title=audit.event,
                detail=_audit_detail(audit),
                status=audit.status,
                created_at=audit.created_at,
            )
            for audit in audits[:3]
        ],
    )


def _list_records(db: Session, model: type[Analysis] | type[Acta], user_id: str | None) -> list:
    statement = select(model).order_by(model.created_at.desc())
    if user_id is not None:
        statement = statement.where(model.user_id == user_id)
    return list(db.scalars(statement).all())


def _list_audits(db: Session, user_id: str | None) -> list[AuditLog]:
    statement = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(20)
    if user_id is not None:
        statement = statement.where(AuditLog.user_id == user_id)
    return list(db.scalars(statement).all())


def _count_since(records: list, since: datetime) -> int:
    return sum(1 for record in records if _as_utc(record.created_at) >= since)


def _count_tasks(actas: list[Acta]) -> tuple[int, int]:
    total = 0
    completed = 0
    for acta in actas:
        tasks = _acta_tasks(acta)
        total += len(tasks)
        completed += sum(1 for task in tasks if bool(task.get("done")))
    return total, completed


def _build_trend(analyses: list[Analysis], actas: list[Acta]) -> list[DashboardTrendPoint]:
    today = datetime.now(UTC).date()
    days = [today - timedelta(days=offset) for offset in range(6, -1, -1)]
    analysis_by_day = _count_by_day(analyses)
    acta_by_day = _count_by_day(actas)
    return [
        DashboardTrendPoint(
            label=_day_label(day),
            analyses=analysis_by_day.get(day, 0),
            actas=acta_by_day.get(day, 0),
        )
        for day in days
    ]


def _build_activity(analyses: list[Analysis], actas: list[Acta]) -> list[DashboardActivityItem]:
    items = [
        DashboardActivityItem(
            title=analysis.filename,
            type="Analisis",
            reference=analysis.mode,
            created_at=analysis.created_at,
        )
        for analysis in analyses[:6]
    ]
    items.extend(
        DashboardActivityItem(
            title=acta.filename,
            type="Acta",
            reference=f"{len(_acta_tasks(acta))} tareas",
            created_at=acta.created_at,
        )
        for acta in actas[:6]
    )
    return sorted(items, key=lambda item: _as_utc(item.created_at), reverse=True)[:6]


def _count_by_day(records: list) -> dict[date, int]:
    result: dict[date, int] = {}
    for record in records:
        day = _as_utc(record.created_at).date()
        result[day] = result.get(day, 0) + 1
    return result


def _acta_tasks(acta: Acta) -> list[dict]:
    if acta.tasks:
        return acta.tasks
    return [task.model_dump() for task in extract_tasks_from_markdown(acta.result)]


def _audit_detail(audit: AuditLog) -> str:
    return f"{audit.module} - {audit.detail}" if audit.detail else audit.module


def _day_label(value: date) -> str:
    return value.strftime("%d/%m")


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
