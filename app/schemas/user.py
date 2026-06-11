from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.schemas.base_schema import TimestampIdSchema
from app.schemas.role import RoleRead


class UserCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: EmailStr
    full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email", mode="after")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).lower()


class UserRead(TimestampIdSchema):
    email: EmailStr
    full_name: str
    dni: str | None = None
    is_active: bool
    must_change_password: bool = False
    role: RoleRead | None = None
    permissions: list[str] = Field(default_factory=list)


class UserAdminCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: EmailStr
    full_name: str = Field(min_length=2, max_length=255)
    dni: str = Field(pattern=r"^\d{8}$")
    role_id: int = Field(ge=1)

    @field_validator("email", mode="after")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).lower()


class UserAdminUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: EmailStr | None = None
    full_name: str | None = Field(default=None, min_length=2, max_length=255)
    dni: str | None = Field(default=None, pattern=r"^\d{8}$")
    role_id: int | None = Field(default=None, ge=1)
    is_active: bool | None = None

    @field_validator("email", mode="after")
    @classmethod
    def normalize_optional_email(cls, value: EmailStr | None) -> str | None:
        return str(value).lower() if value is not None else None


class UserProfileUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    full_name: str = Field(min_length=2, max_length=255)
