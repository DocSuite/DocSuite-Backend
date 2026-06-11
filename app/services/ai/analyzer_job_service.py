import asyncio
from pathlib import Path
from threading import Lock, Thread

from sqlalchemy import select, update

from app.core.config import get_settings
from app.db.session import get_session_local
from app.models.job import AnalyzerJobRecord
from app.schemas.analysis import AnalysisJobRead, AnalysisMode
from app.services.ai.analyzer_service import analyze_document_with_progress
from app.services.db.analysis_service import create_analysis
from app.services.db.audit_service import create_audit_event

_progress: dict[str, tuple[int, str]] = {}
_active_jobs: dict[str, int] = {}
_lock = Lock()


def _acquire_slot(user_id: str) -> bool:
    settings = get_settings()
    with _lock:
        current = _active_jobs.get(user_id, 0)
        if current >= settings.max_concurrent_jobs_per_user:
            return False
        _active_jobs[user_id] = current + 1
        return True


def _release_slot(user_id: str) -> None:
    with _lock:
        _active_jobs[user_id] = max(0, _active_jobs.get(user_id, 1) - 1)


def create_analyzer_job(user_id: str, filename: str, file_path: Path, mode: AnalysisMode) -> AnalysisJobRead:
    if not _acquire_slot(user_id):
        settings = get_settings()
        raise RuntimeError(
            f"Limite de {settings.max_concurrent_jobs_per_user} jobs simultaneos alcanzado. "
            "Espera a que termine el actual."
        )

    db = get_session_local()()
    try:
        record = AnalyzerJobRecord(
            user_id=user_id,
            filename=filename,
            file_path=str(file_path.resolve()),
            mode=mode.value,
            status="queued",
            progress=0,
            message="En cola",
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        job_id = record.id
        create_audit_event(
            db,
            user_id,
            "Analisis iniciado",
            "DocAnalyzer",
            detail=filename,
            resource_id=job_id,
        )
    except Exception:
        _release_slot(user_id)
        raise
    finally:
        db.close()

    with _lock:
        _progress[job_id] = (0, "En cola")

    Thread(target=_run_analyzer_job, args=(job_id, user_id), daemon=True).start()
    return AnalysisJobRead(job_id=job_id, status="queued", progress=0, message="En cola")


def get_analyzer_job(job_id: str, user_id: str) -> AnalysisJobRead | None:
    with _lock:
        mem = _progress.get(job_id)

    db = get_session_local()()
    try:
        record = db.scalars(
            select(AnalyzerJobRecord).where(AnalyzerJobRecord.id == job_id, AnalyzerJobRecord.user_id == user_id)
        ).first()
        if record is None:
            return None

        progress = record.progress
        message = record.message
        if mem is not None:
            progress, message = mem

        return AnalysisJobRead(
            job_id=record.id,
            status=record.status,
            progress=progress,
            message=message,
            analysis_id=record.analysis_id,
            error=record.error,
        )
    finally:
        db.close()


def _set_progress(job_id: str, progress: int, message: str) -> None:
    with _lock:
        _progress[job_id] = (progress, message)
    db = get_session_local()()
    try:
        db.execute(
            update(AnalyzerJobRecord)
            .where(AnalyzerJobRecord.id == job_id)
            .values(status="running", progress=progress, message=message)
        )
        db.commit()
    finally:
        db.close()


def _persist_completed(job_id: str, analysis_id: str) -> None:
    db = get_session_local()()
    try:
        db.execute(
            update(AnalyzerJobRecord)
            .where(AnalyzerJobRecord.id == job_id)
            .values(status="completed", progress=100, message="Completado", analysis_id=analysis_id)
        )
        db.commit()
    finally:
        db.close()
    with _lock:
        _progress.pop(job_id, None)


def _persist_failed(job_id: str, error: str) -> None:
    db = get_session_local()()
    try:
        db.execute(
            update(AnalyzerJobRecord)
            .where(AnalyzerJobRecord.id == job_id)
            .values(status="failed", progress=100, message="Fallido", error=error[:1000])
        )
        db.commit()
    finally:
        db.close()
    with _lock:
        _progress.pop(job_id, None)


def _run_analyzer_job(job_id: str, user_id: str) -> None:
    db_read = get_session_local()()
    try:
        record = db_read.scalars(select(AnalyzerJobRecord).where(AnalyzerJobRecord.id == job_id)).first()
        if record is None:
            return
        filename = record.filename
        file_path = Path(record.file_path)
        mode = AnalysisMode(record.mode)
    finally:
        db_read.close()

    try:
        _set_progress(job_id, 5, "Preparando analisis")
        payload = asyncio.run(
            analyze_document_with_progress(
                file_path,
                filename,
                mode,
                progress_callback=lambda progress, message: _set_progress(job_id, progress, message),
            )
        )

        _set_progress(job_id, 92, "Guardando resultado")
        db = get_session_local()()
        try:
            analysis = create_analysis(db, user_id, payload)
            analysis_id = analysis.id
            create_audit_event(
                db,
                user_id,
                "Documento analizado",
                "DocAnalyzer",
                detail=analysis.filename,
                resource_id=analysis.id,
            )
        finally:
            db.close()

        _persist_completed(job_id, analysis_id)
    except Exception as exc:
        _persist_failed(job_id, str(exc))
        db = get_session_local()()
        try:
            create_audit_event(
                db,
                user_id,
                "Analisis fallido",
                "DocAnalyzer",
                detail=str(exc)[:1000],
                resource_id=job_id,
                status="error",
            )
        finally:
            db.close()
    finally:
        _release_slot(user_id)
