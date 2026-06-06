from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import AdminUser, DbSession
from app.core.config import get_settings
from app.core.exceptions import DocSuiteException
from app.schemas.role import (
    RoleCreate,
    RolePermissionRead,
    RolePermissionUpdate,
    RoleRead,
    RoleUpdate,
)
from app.schemas.user import UserAdminCreate, UserAdminUpdate, UserRead
from app.services.db.audit_service import create_audit_event
from app.services.db.role_service import (
    create_role,
    delete_role,
    get_role_permissions,
    get_user_permissions,
    list_roles,
    save_role_permissions,
    update_role,
)
from app.services.db.user_service import (
    create_user_by_admin,
    get_user_by_id,
    list_users,
    update_user_access,
)
from app.services.storage.temp_cleaner import CleanupMode, cleanup_storage

router = APIRouter()

CleanupModeQuery = Annotated[
    CleanupMode,
    Query(
        description=(
            "all - elimina todos los archivos; "
            "week - elimina archivos con mas de 7 dias; "
            "month - elimina archivos con mas de 30 dias"
        ),
    ),
]


@router.get("/users", response_model=list[UserRead])
def get_users(db: DbSession, current_user: AdminUser) -> list[UserRead]:
    users = []
    for user in list_users(db):
        data = UserRead.model_validate(user)
        data.permissions = get_user_permissions(db, user)
        users.append(data)
    return users


@router.post("/users", response_model=UserRead, status_code=201)
def post_user(
    payload: UserAdminCreate,
    db: DbSession,
    current_user: AdminUser,
) -> UserRead:
    user = create_user_by_admin(db, payload)
    create_audit_event(db, current_user.id, "Usuario creado", "Admin", detail=user.email)
    data = UserRead.model_validate(user)
    data.permissions = get_user_permissions(db, user)
    return data


@router.patch("/users/{user_id}", response_model=UserRead)
def patch_user_access(
    user_id: str,
    payload: UserAdminUpdate,
    db: DbSession,
    current_user: AdminUser,
) -> UserRead:
    user = get_user_by_id(db, user_id)
    if user is None:
        raise DocSuiteException("Usuario no encontrado", status_code=404)

    user = update_user_access(
        db,
        user,
        email=str(payload.email) if payload.email is not None else None,
        full_name=payload.full_name,
        dni=payload.dni,
        role_id=payload.role_id,
        is_active=payload.is_active,
    )
    create_audit_event(db, current_user.id, "Usuario actualizado", "Admin", detail=user.email)
    data = UserRead.model_validate(user)
    data.permissions = get_user_permissions(db, user)
    return data


@router.get("/roles", response_model=list[RoleRead])
def get_roles(db: DbSession, current_user: AdminUser) -> list[RoleRead]:
    return [RoleRead.model_validate(role) for role in list_roles(db)]


@router.post("/roles", response_model=RoleRead, status_code=201)
def post_role(payload: RoleCreate, db: DbSession, current_user: AdminUser) -> RoleRead:
    role = create_role(db, payload)
    create_audit_event(db, current_user.id, "Rol creado", "Admin", detail=role.name)
    return RoleRead.model_validate(role)


@router.patch("/roles/{role_id}", response_model=RoleRead)
def patch_role(
    role_id: int,
    payload: RoleUpdate,
    db: DbSession,
    current_user: AdminUser,
) -> RoleRead:
    role = update_role(db, role_id, payload)
    create_audit_event(db, current_user.id, "Rol actualizado", "Admin", detail=role.name)
    return RoleRead.model_validate(role)


@router.delete("/roles/{role_id}", status_code=204)
def remove_role(role_id: int, db: DbSession, current_user: AdminUser) -> None:
    delete_role(db, role_id)
    create_audit_event(db, current_user.id, "Rol eliminado", "Admin", detail=str(role_id))


@router.get("/roles/{role_id}/permissions", response_model=list[RolePermissionRead])
def get_role_permission_matrix(
    role_id: int,
    db: DbSession,
    current_user: AdminUser,
) -> list[RolePermissionRead]:
    return get_role_permissions(db, role_id)


@router.put("/roles/{role_id}/permissions", response_model=list[RolePermissionRead])
def put_role_permission_matrix(
    role_id: int,
    payload: list[RolePermissionUpdate],
    db: DbSession,
    current_user: AdminUser,
) -> list[RolePermissionRead]:
    permissions = save_role_permissions(db, role_id, payload)
    create_audit_event(db, current_user.id, "Permisos actualizados", "Admin", detail=str(role_id))
    return permissions


@router.post("/storage/cleanup")
def run_storage_cleanup(
    current_user: AdminUser,
    mode: CleanupMode = Query(
        default=CleanupMode.week,
        description=(
            "all — elimina todos los archivos; "
            "week — elimina archivos con más de 7 días; "
            "month — elimina archivos con más de 30 días"
        ),
    ),
) -> dict:
    settings = get_settings()
    result = cleanup_storage(
        upload_dir=settings.upload_dir.resolve(),
        temp_dir=settings.temp_dir.resolve(),
        processed_dir=settings.processed_dir.resolve(),
        mode=mode,
    )
    return result.summary()
