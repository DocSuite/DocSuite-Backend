from pathlib import Path
from threading import Lock, Thread

from sqlalchemy import select, update

from app.db.session import get_session_local
from app.models.job import ActaJobRecord
from app.schemas.acta import ActaJobRead
from app.services.ai.acta_service import generate_acta_sync
from app.services.audio.diarizer import diarize_audio_sync
from app.services.audio.preprocessor import preprocess_audio
from app.services.audio.transcriber import transcribe_audio_sync
from app.services.db.acta_service import create_acta

_progress: dict[str, tuple[int, str]] = {}
_lock = Lock()


def create_acta_job(user_id: str, filename: str, file_path: Path) -> ActaJobRead:
    db = get_session_local()()
    try:
        record = ActaJobRecord(
            user_id=user_id,
            filename=filename,
            file_path=str(file_path.resolve()),
            status="queued",
            progress=0,
            message="En cola",
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        job_id = record.id
    finally:
        db.close()

    with _lock:
        _progress[job_id] = (0, "En cola")

    Thread(target=_run_acta_job, args=(job_id,), daemon=True).start()
    return ActaJobRead(job_id=job_id, status="queued", progress=0, message="En cola")


def get_acta_job(job_id: str, user_id: str) -> ActaJobRead | None:
    with _lock:
        mem = _progress.get(job_id)

    if mem is not None:
        db = get_session_local()()
        try:
            record = db.scalars(
                select(ActaJobRecord).where(ActaJobRecord.id == job_id, ActaJobRecord.user_id == user_id)
            ).first()
            if record is None:
                return None
            progress, message = mem
            return ActaJobRead(
                job_id=job_id,
                status=record.status,
                progress=progress,
                message=message,
                acta_id=record.acta_id,
                error=record.error,
            )
        finally:
            db.close()

    db = get_session_local()()
    try:
        record = db.scalars(
            select(ActaJobRecord).where(ActaJobRecord.id == job_id, ActaJobRecord.user_id == user_id)
        ).first()
        if record is None:
            return None
        return ActaJobRead(
            job_id=record.id,
            status=record.status,
            progress=record.progress,
            message=record.message,
            acta_id=record.acta_id,
            error=record.error,
        )
    finally:
        db.close()


def _set_progress(job_id: str, progress: int, message: str) -> None:
    with _lock:
        _progress[job_id] = (progress, message)


def _persist_completed(job_id: str, acta_id: str) -> None:
    db = get_session_local()()
    try:
        db.execute(
            update(ActaJobRecord)
            .where(ActaJobRecord.id == job_id)
            .values(status="completed", progress=100, message="Completado", acta_id=acta_id)
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
            update(ActaJobRecord)
            .where(ActaJobRecord.id == job_id)
            .values(status="failed", progress=100, message="Fallido", error=error[:1000])
        )
        db.commit()
    finally:
        db.close()
    with _lock:
        _progress.pop(job_id, None)


def _run_acta_job(job_id: str) -> None:
    db_read = get_session_local()()
    try:
        record = db_read.scalars(select(ActaJobRecord).where(ActaJobRecord.id == job_id)).first()
        if record is None:
            return
        user_id = record.user_id
        filename = record.filename
        file_path = Path(record.file_path)
    finally:
        db_read.close()

    preprocessed: Path | None = None
    try:
        _set_progress(job_id, 10, "Preprocesando audio")
        preprocessed = preprocess_audio(file_path)

        _set_progress(job_id, 22, "Transcribiendo audio")
        transcription = transcribe_audio_sync(preprocessed)

        _set_progress(job_id, 55, "Identificando participantes")
        diarization = diarize_audio_sync(preprocessed)

        _set_progress(job_id, 80, "Generando acta")
        acta_payload = generate_acta_sync(filename, transcription, diarization)

        db = get_session_local()()
        try:
            acta = create_acta(db, user_id, acta_payload)
            acta_id = acta.id
        finally:
            db.close()

        _persist_completed(job_id, acta_id)

    except Exception as exc:
        _persist_failed(job_id, str(exc))

    finally:
        if preprocessed is not None:
            preprocessed.unlink(missing_ok=True)


def mark_orphan_jobs_failed() -> None:
    db = get_session_local()()
    try:
        db.execute(
            update(ActaJobRecord)
            .where(ActaJobRecord.status.in_(["queued", "running"]))
            .values(status="failed", message="Servidor reiniciado", error="El servidor se reinició durante el procesamiento")
        )
        db.commit()
    finally:
        db.close()
