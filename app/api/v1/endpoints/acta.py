from fastapi import APIRouter, File, UploadFile, status

from app.api.deps import CurrentUser, DbSession
from app.core.exceptions import DocSuiteException
from app.schemas.acta import ActaJobRead, ActaRead, SpeakerNameMap
from app.services.ai.acta_service import generate_acta
from app.services.audio.acta_job_service import create_acta_job, get_acta_job
from app.services.audio.audio_utils import AUDIO_EXTENSIONS
from app.services.audio.diarizer import diarize_audio
from app.services.audio.transcriber import transcribe_audio
from app.services.db.acta_service import create_acta, get_acta_by_id, update_speaker_names
from app.services.storage.file_service import save_upload_file

router = APIRouter()


@router.post("/jobs", response_model=ActaJobRead, status_code=status.HTTP_202_ACCEPTED)
async def create_meeting_acta_job(
    current_user: CurrentUser,
    file: UploadFile = File(...),
) -> ActaJobRead:
    saved_file = await save_upload_file(file, allowed_extensions=AUDIO_EXTENSIONS)
    return create_acta_job(current_user.id, file.filename or saved_file.name, saved_file)


@router.get("/jobs/{job_id}", response_model=ActaJobRead)
def read_meeting_acta_job(job_id: str, current_user: CurrentUser) -> ActaJobRead:
    job = get_acta_job(job_id, current_user.id)
    if job is None:
        raise DocSuiteException("Job no encontrado", status_code=status.HTTP_404_NOT_FOUND)
    return job


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
