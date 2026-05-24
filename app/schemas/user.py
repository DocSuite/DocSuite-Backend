from pydantic import BaseModel, EmailStr, Field

from app.schemas.base_schema import TimestampIdSchema


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class UserRead(TimestampIdSchema):
    email: EmailStr
    full_name: str
    is_active: bool
