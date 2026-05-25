import asyncio
import json
import urllib.parse
from collections.abc import AsyncGenerator

from fastapi import APIRouter, File, UploadFile, status
from fastapi.responses import StreamingResponse

from app.api.deps import CurrentUser, DbSession
from app.core.exceptions import DocSuiteException
from app.schemas.acta import ActaJobRead, ActaRead, ActaUpdate, SpeakerNameMap
from app.services.ai.acta_service import generate_acta
from app.services.audio.acta_job_service import create_acta_job, get_acta_job
from app.services.audio.audio_utils import AUDIO_EXTENSIONS
from app.services.audio.diarizer import diarize_audio
from app.services.audio.transcriber import transcribe_audio
from app.services.db.acta_service import create_acta, get_acta_by_id, update_acta_content, update_speaker_names
from app.services.export.docx_service import markdown_to_docx
from app.services.storage.file_service import save_upload_file

router = APIRouter()


@router.post("/jobs", response_model=ActaJobRead, status_code=status.HTTP_202_ACCEPTED)
async def create_meeting_acta_job(
    current_user: CurrentUser,
    file: UploadFile = File(...),
) -> ActaJobRead:
    saved_file = await save_upload_file(file, allowed_extensions=AUDIO_EXTENSIONS)
    try:
        return create_acta_job(current_user.id, file.filename or saved_file.name, saved_file)
    except RuntimeError as exc:
        raise DocSuiteException(str(exc), status_code=status.HTTP_429_TOO_MANY_REQUESTS) from exc


@router.get("/jobs/{job_id}", response_model=ActaJobRead)
def read_meeting_acta_job(job_id: str, current_user: CurrentUser) -> ActaJobRead:
    job = get_acta_job(job_id, current_user.id)
    if job is None:
        raise DocSuiteException("Job no encontrado", status_code=status.HTTP_404_NOT_FOUND)
    return job


@router.get("/jobs/{job_id}/stream")
async def stream_job_progress(job_id: str, current_user: CurrentUser) -> StreamingResponse:
    user_id = current_user.id

    async def _generator() -> AsyncGenerator[str, None]:
        while True:
            job = get_acta_job(job_id, user_id)
            if job is None:
                yield f"data: {json.dumps({'error': 'Job no encontrado'})}\n\n"
                break

            payload = {
                "progress": job.progress,
                "status": job.status,
                "message": job.message,
                "acta_id": job.acta_id,
                "error": job.error,
            }
            yield f"data: {json.dumps(payload)}\n\n"

            if job.status in ("completed", "failed"):
                break

            await asyncio.sleep(1)

    return StreamingResponse(
        _generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/", response_model=ActaRead, status_code=status.HTTP_201_CREATED)
async def create_meeting_acta(
    db: DbSession,
    current_user: CurrentUser,
    file: UploadFile = File(...),
) -> ActaRead:
    saved_file = await save_upload_file(file, allowed_extensions=AUDIO_EXTENSIONS)
    transcription = await transcribe_audio(saved_file)
    diarization = await diarize_audio(saved_file)
    acta_payload = await generate_acta(file.filename or saved_file.name, transcription, diarization)
    acta = create_acta(db, current_user.id, acta_payload)
    return ActaRead.model_validate(acta)


@router.get("/{acta_id}", response_model=ActaRead)
def read_acta(acta_id: str, db: DbSession, current_user: CurrentUser) -> ActaRead:
    acta = get_acta_by_id(db, acta_id, current_user.id)
    if acta is None:
        raise DocSuiteException("Acta no encontrada", status_code=status.HTTP_404_NOT_FOUND)
    return ActaRead.model_validate(acta)


@router.patch("/{acta_id}", response_model=ActaRead)
def edit_acta(
    acta_id: str,
    body: ActaUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> ActaRead:
    acta = get_acta_by_id(db, acta_id, current_user.id)
    if acta is None:
        raise DocSuiteException("Acta no encontrada", status_code=status.HTTP_404_NOT_FOUND)
    acta = update_acta_content(db, acta, body)
    return ActaRead.model_validate(acta)


@router.get("/{acta_id}/export/docx")
def export_acta_docx(acta_id: str, db: DbSession, current_user: CurrentUser) -> StreamingResponse:
    acta = get_acta_by_id(db, acta_id, current_user.id)
    if acta is None:
        raise DocSuiteException("Acta no encontrada", status_code=status.HTTP_404_NOT_FOUND)

    buf = markdown_to_docx(acta.result, acta.filename)
    safe_name = urllib.parse.quote(acta.filename.rsplit(".", 1)[0] + "_acta.docx")
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{safe_name}"},
    )


@router.post("/{acta_id}/regenerate", response_model=ActaRead)
async def regenerate_acta(acta_id: str, db: DbSession, current_user: CurrentUser) -> ActaRead:
    acta = get_acta_by_id(db, acta_id, current_user.id)
    if acta is None:
        raise DocSuiteException("Acta no encontrada", status_code=status.HTTP_404_NOT_FOUND)
    acta_payload = await generate_acta(acta.filename, acta.transcription, acta.diarization)
    acta = update_acta_content(db, acta, ActaUpdate(result=acta_payload.result))
    return ActaRead.model_validate(acta)


@router.patch("/{acta_id}/speakers", response_model=ActaRead)
def assign_speaker_names(
    acta_id: str,
    body: SpeakerNameMap,
    db: DbSession,
    current_user: CurrentUser,
) -> ActaRead:
    acta = get_acta_by_id(db, acta_id, current_user.id)
    if acta is None:
        raise DocSuiteException("Acta no encontrada", status_code=status.HTTP_404_NOT_FOUND)
    acta = update_speaker_names(db, acta, body.names)
    return ActaRead.model_validate(acta)
