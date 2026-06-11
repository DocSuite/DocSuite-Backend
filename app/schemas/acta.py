from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.base_schema import TimestampIdSchema


class TaskItem(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    description: str = Field(min_length=1, max_length=500)
    owner: str | None = Field(default=None, max_length=120)
    due_date: str | None = Field(default=None, max_length=40)
    done: bool = False


class ActaCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    filename: str = Field(min_length=1, max_length=255)
    duration_seconds: float | None = None
    transcription: str = Field(min_length=1)
    diarization: dict | None = None
    result: str = Field(min_length=1)
    tasks: list[TaskItem] = Field(default_factory=list)


class ActaRead(TimestampIdSchema):
    filename: str
    duration_seconds: float | None
    transcription: str
    diarization: dict | None
    result: str
    tasks: list[dict]


class ActaJobRead(BaseModel):
    job_id: str
    status: str
    progress: int = Field(ge=0, le=100)
    message: str
    acta_id: str | None = None
    error: str | None = None


class ActaUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    transcription: str | None = Field(default=None, description="Texto transcrito revisado")
    result: str | None = Field(default=None, description="Texto del acta en Markdown")
    tasks: list[TaskItem] | None = Field(default=None, description="Lista de tareas actualizada")

    @model_validator(mode="after")
    def require_one_field(self) -> "ActaUpdate":
        if self.transcription is None and self.result is None and self.tasks is None:
            raise ValueError("Debes enviar al menos un campo para actualizar")
        return self


class SpeakerNameMap(BaseModel):
    names: dict[str, str] = Field(
        ...,
        min_length=1,
        description="Mapeo de speaker_id a nombre real. Ej: {'SPEAKER_00': 'Dr. Luis Lenin'}",
        examples=[{"SPEAKER_00": "Dr. Luis Lenin", "SPEAKER_01": "Lic. María García"}],
    )
