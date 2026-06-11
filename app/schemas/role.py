from pydantic import BaseModel, ConfigDict, Field

from app.schemas.base_schema import ORMBase


class RoleRead(ORMBase):
    id: int
    name: str
    description: str | None = None
    is_system: bool


class RoleCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=2, max_length=80)
    description: str | None = Field(default=None, max_length=250)


class RoleUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=2, max_length=80)
    description: str | None = Field(default=None, max_length=250)


class RolePermissionRead(BaseModel):
    view_id: int
    code: str
    name: str
    route: str
    group: str | None = None
    can_read: bool
    can_create: bool
    can_update: bool
    can_delete: bool


class RolePermissionUpdate(BaseModel):
    view_id: int = Field(ge=1)
    can_read: bool = False
    can_create: bool = False
    can_update: bool = False
    can_delete: bool = False
