from pydantic import BaseModel, EmailStr, Field

from app.schemas.base_schema import TimestampIdSchema
from app.schemas.role import RoleRead


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class UserRead(TimestampIdSchema):
    email: EmailStr
    full_name: str
    dni: str | None = None
    is_active: bool
    must_change_password: bool = False
    role: RoleRead | None = None
    permissions: list[str] = Field(default_factory=list)


class UserAdminCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=255)
    dni: str = Field(pattern=r"^\d{8}$")
    role_id: int


class UserAdminUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = Field(default=None, min_length=2, max_length=255)
    dni: str | None = Field(default=None, pattern=r"^\d{8}$")
    role_id: int | None = None
    is_active: bool | None = None


class UserProfileUpdate(BaseModel):
    full_name: str = Field(min_length=2, max_length=255)
