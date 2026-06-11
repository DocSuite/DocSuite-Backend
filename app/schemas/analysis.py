from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.base_schema import TimestampIdSchema


class AnalysisMode(StrEnum):
    general = "general"
    academic = "academic"


class AnalysisCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    filename: str = Field(min_length=1, max_length=255)
    mode: AnalysisMode
    extracted_text: str = Field(min_length=1)
    result: str = Field(min_length=1)


class AnalysisRead(TimestampIdSchema):
    filename: str
    mode: str
    extracted_text: str
    result: str
