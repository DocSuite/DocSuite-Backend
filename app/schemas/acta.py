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
