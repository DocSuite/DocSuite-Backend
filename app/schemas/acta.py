from pydantic import BaseModel, Field

from app.schemas.base_schema import TimestampIdSchema


class TaskItem(BaseModel):
    description: str
    owner: str | None = None
    due_date: str | None = None
    done: bool = False


class ActaCreate(BaseModel):
    filename: str
    transcription: str
    diarization: dict | None = None
    result: str
    tasks: list[TaskItem] = Field(default_factory=list)


class ActaRead(TimestampIdSchema):
    filename: str
    transcription: str
    diarization: dict | None
    result: str
    tasks: list[dict]


class ActaJobRead(BaseModel):
    job_id: str
    status: str
    progress: int
    message: str
    acta_id: str | None = None
    error: str | None = None


class SpeakerNameMap(BaseModel):
    names: dict[str, str] = Field(
        ...,
        description="Mapeo de speaker_id a nombre real. Ej: {'SPEAKER_00': 'Dr. Luis Lenin'}",
        examples=[{"SPEAKER_00": "Dr. Luis Lenin", "SPEAKER_01": "Lic. María García"}],
    )
