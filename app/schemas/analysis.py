from enum import StrEnum

from pydantic import BaseModel

from app.schemas.base_schema import TimestampIdSchema


class AnalysisMode(StrEnum):
    general = "general"
    academic = "academic"


class AnalysisCreate(BaseModel):
    filename: str
    mode: AnalysisMode
    extracted_text: str
    result: str


class AnalysisRead(TimestampIdSchema):
    filename: str
    mode: str
    extracted_text: str
    result: str
