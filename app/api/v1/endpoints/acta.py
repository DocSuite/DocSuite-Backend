from fastapi import APIRouter, File, UploadFile, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.acta import ActaRead
from app.services.ai.acta_service import generate_acta
from app.services.audio.diarizer import diarize_audio
from app.services.audio.transcriber import transcribe_audio
from app.services.db.acta_service import create_acta
from app.services.storage.file_service import save_upload_file

router = APIRouter()


@router.post("/", response_model=ActaRead, status_code=status.HTTP_201_CREATED)
async def create_meeting_acta(
    db: DbSession,
    current_user: CurrentUser,
    file: UploadFile = File(...),
) -> ActaRead:
    saved_file = await save_upload_file(file)
    transcription = await transcribe_audio(saved_file)
    diarization = await diarize_audio(saved_file)
    acta_payload = await generate_acta(file.filename or saved_file.name, transcription, diarization)
    acta = create_acta(db, current_user.id, acta_payload)
    return ActaRead.model_validate(acta)
