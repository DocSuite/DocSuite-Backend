from collections.abc import Iterable

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import DocSuiteException
from app.models.role import AppView, Role, RoleViewPermission
from app.models.user import User
from app.schemas.role import RoleCreate, RolePermissionRead, RolePermissionUpdate, RoleUpdate

ADMIN_ROLE_NAME = "admin"
DOCENTE_ROLE_NAME = "docente"
ESTUDIANTE_ROLE_NAME = "estudiante"
DEFAULT_ROLE_NAME = DOCENTE_ROLE_NAME

SYSTEM_ROLES = [
    {"id": 1, "name": ADMIN_ROLE_NAME, "description": "Administrador del sistema"},
    {"id": 2, "name": DOCENTE_ROLE_NAME, "description": "Docente"},
    {"id": 3, "name": ESTUDIANTE_ROLE_NAME, "description": "Estudiante"},
]

SYSTEM_VIEWS = [
    {
        "id": 1,
        "code": "dashboard",
        "name": "Dashboard",
        "route": "/dashboard",
        "group": "General",
        "order": 1,
    },
    {
        "id": 2,
        "code": "profile",
        "name": "Perfil",
        "route": "/profile",
        "group": "General",
        "order": 2,
    },
    {
        "id": 3,
        "code": "doc_acta",
        "name": "DocActa",
        "route": "/doc-acta",
        "group": "Documentos",
        "order": 3,
    },
    {
        "id": 4,
        "code": "history",
        "name": "Historial",
        "route": "/history",
        "group": "Documentos",
        "order": 4,
    },
    {
        "id": 5,
        "code": "audits",
        "name": "Auditorias",
        "route": "/audits",
        "group": "Admin",
        "order": 5,
    },
    {
        "id": 6,
        "code": "admin_users",
        "name": "Usuarios",
        "route": "/admin/users",
        "group": "Admin",
        "order": 6,
    },
    {
        "id": 7,
        "code": "admin_roles",
        "name": "Roles",
        "route": "/admin/roles",
        "group": "Admin",
        "order": 7,
    },
    {
        "id": 8,
        "code": "admin_storage",
        "name": "Storage",
        "route": "/admin/storage",
        "group": "Admin",
        "order": 8,
    },
    {
        "id": 9,
        "code": "doc_analyzer",
        "name": "DocAnalyzer",
        "route": "/doc-analyzer",
        "group": "Documentos",
        "order": 9,
    },
]

ROLE_VIEW_DEFAULTS = {
    ADMIN_ROLE_NAME: {
        "dashboard": (True, True, True, True),
        "profile": (True, True, True, True),
        "doc_acta": (True, True, True, True),
        "history": (True, True, True, True),
        "audits": (True, False, False, False),
        "admin_users": (True, True, True, True),
        "admin_roles": (True, True, True, True),
        "admin_storage": (True, True, True, True),
        "doc_analyzer": (True, True, True, True),
    },
    DOCENTE_ROLE_NAME: {
        "dashboard": (True, False, False, False),
        "profile": (True, False, True, False),
        "doc_acta": (True, True, True, False),
        "history": (True, False, False, False),
        "doc_analyzer": (True, True, False, False),
    },
    ESTUDIANTE_ROLE_NAME: {
        "dashboard": (True, False, False, False),
        "profile": (True, False, True, False),
        "history": (True, False, False, False),
    },
}


def get_role_by_name(db: Session, name: str) -> Role | None:
    return db.scalar(select(Role).where(Role.name == normalize_role_name(name)))


def get_default_role(db: Session) -> Role:
    role = get_role_by_name(db, DEFAULT_ROLE_NAME)
    if role is None:
        raise DocSuiteException("Rol por defecto no configurado")
    return role


def list_roles(db: Session) -> list[Role]:
    return list(db.scalars(select(Role).order_by(Role.is_system.desc(), Role.name.asc())).all())


def create_role(db: Session, payload: RoleCreate) -> Role:
    name = normalize_role_name(payload.name)
    if get_role_by_name(db, name) is not None:
        raise DocSuiteException("Ya existe un rol con ese nombre")

    role = Role(name=name, description=clean_description(payload.description), is_system=False)
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


def update_role(db: Session, role_id: int, payload: RoleUpdate) -> Role:
    role = db.get(Role, role_id)
    if role is None:
        raise DocSuiteException("Rol no encontrado", status_code=404)

    if payload.name is not None and not role.is_system:
        name = normalize_role_name(payload.name)
        existing = get_role_by_name(db, name)
        if existing is not None and existing.id != role.id:
            raise DocSuiteException("Ya existe un rol con ese nombre")
        role.name = name

    if payload.description is not None:
        role.description = clean_description(payload.description)

    db.commit()
    db.refresh(role)
    return role


def delete_role(db: Session, role_id: int) -> None:
    role = db.get(Role, role_id)
    if role is None:
        raise DocSuiteException("Rol no encontrado", status_code=404)
    if role.is_system:
        raise DocSuiteException("No se puede eliminar un rol del sistema")
    if db.scalar(select(User.id).where(User.role_id == role.id).limit(1)) is not None:
        raise DocSuiteException("No se puede eliminar un rol asignado a usuarios")

    db.delete(role)
    db.commit()


def get_role_permissions(db: Session, role_id: int) -> list[RolePermissionRead]:
    role = db.get(Role, role_id)
    if role is None:
        raise DocSuiteException("Rol no encontrado", status_code=404)

    permissions = db.scalars(
        select(RoleViewPermission)
        .options(joinedload(RoleViewPermission.view))
        .where(RoleViewPermission.role_id == role_id)
    ).all()
    by_view_id = {permission.view_id: permission for permission in permissions}
    views = db.scalars(
        select(AppView)
        .where(AppView.active.is_(True))
        .order_by(AppView.order.asc(), AppView.name.asc())
    )

    result: list[RolePermissionRead] = []
    for view in views:
        permission = by_view_id.get(view.id)
        result.append(
            RolePermissionRead(
                view_id=view.id,
                code=view.code,
                name=view.name,
                route=view.route,
                group=view.group,
                can_read=permission.can_read if permission else False,
                can_create=permission.can_create if permission else False,
                can_update=permission.can_update if permission else False,
                can_delete=permission.can_delete if permission else False,
            )
        )
    return result


def save_role_permissions(
    db: Session,
    role_id: int,
    payload: Iterable[RolePermissionUpdate],
) -> list[RolePermissionRead]:
    role = db.get(Role, role_id)
    if role is None:
        raise DocSuiteException("Rol no encontrado", status_code=404)

    db.execute(delete(RoleViewPermission).where(RoleViewPermission.role_id == role.id))
    for item in payload:
        view = db.get(AppView, item.view_id)
        if view is None:
            raise DocSuiteException("Vista no encontrada", status_code=404)
        db.add(
            RoleViewPermission(
                role_id=role.id,
                view_id=view.id,
                can_read=item.can_read,
                can_create=item.can_create,
                can_update=item.can_update,
                can_delete=item.can_delete,
            )
        )

    db.commit()
    return get_role_permissions(db, role.id)


def get_user_permissions(db: Session, user: User) -> list[str]:
    if user.role and user.role.name == ADMIN_ROLE_NAME:
        return ["*"]

    permissions = db.scalars(
        select(RoleViewPermission)
        .options(joinedload(RoleViewPermission.view))
        .where(RoleViewPermission.role_id == user.role_id)
    ).all()

    result: list[str] = []
    for permission in permissions:
        route = permission.view.route
        if permission.can_read:
            result.append(route)
        if permission.can_create:
            result.append(f"{route}:w")
        if permission.can_update:
            result.append(f"{route}:e")
        if permission.can_delete:
            result.append(f"{route}:d")
    return result


def user_has_permission(db: Session, user: User, route: str, action: str = "read") -> bool:
    if user.role and user.role.name == ADMIN_ROLE_NAME:
        return True

    permission = db.scalar(
        select(RoleViewPermission)
        .join(AppView)
        .where(RoleViewPermission.role_id == user.role_id, AppView.route == route)
    )
    if permission is None:
        return False

    return {
        "read": permission.can_read,
        "create": permission.can_create,
        "update": permission.can_update,
        "delete": permission.can_delete,
    }.get(action, False)


def seed_access_control(db: Session, admin_email: str) -> None:
    for role_data in SYSTEM_ROLES:
        role = db.get(Role, role_data["id"])
        if role is None:
            role = Role(id=role_data["id"], name=role_data["name"], is_system=True)
            db.add(role)
        role.description = role_data["description"]
        role.is_system = True

    for view_data in SYSTEM_VIEWS:
        view = db.get(AppView, view_data["id"])
        if view is None:
            view = AppView(id=view_data["id"], code=view_data["code"])
            db.add(view)
        view.name = view_data["name"]
        view.route = view_data["route"]
        view.group = view_data["group"]
        view.order = view_data["order"]
        view.active = True

    db.flush()
    _seed_role_permissions(db)

    docente_role = get_role_by_name(db, DOCENTE_ROLE_NAME)
    admin_role = get_role_by_name(db, ADMIN_ROLE_NAME)
    if docente_role is not None:
        db.execute(
            User.__table__.update().where(User.role_id.is_(None)).values(role_id=docente_role.id)
        )
    if admin_role is not None:
        db.execute(
            User.__table__.update().where(User.email == admin_email).values(role_id=admin_role.id)
        )
    db.commit()


def _seed_role_permissions(db: Session) -> None:
    role_by_name = {role.name: role for role in db.scalars(select(Role)).all()}
    view_by_code = {view.code: view for view in db.scalars(select(AppView)).all()}

    for role_name, view_permissions in ROLE_VIEW_DEFAULTS.items():
        role = role_by_name.get(role_name)
        if role is None:
            continue
        for view_code, flags in view_permissions.items():
            view = view_by_code.get(view_code)
            if view is None:
                continue
            permission = db.scalar(
                select(RoleViewPermission).where(
                    RoleViewPermission.role_id == role.id,
                    RoleViewPermission.view_id == view.id,
                )
            )
            if permission is None:
                permission = RoleViewPermission(role_id=role.id, view_id=view.id)
                db.add(permission)
            (
                permission.can_read,
                permission.can_create,
                permission.can_update,
                permission.can_delete,
            ) = flags


def normalize_role_name(name: str) -> str:
    normalized = name.strip().lower().replace(" ", "_")
    if not normalized or len(normalized) > 80:
        raise DocSuiteException("Nombre de rol invalido")
    if not all(part.isalnum() for part in normalized.split("_")):
        raise DocSuiteException("Nombre de rol invalido")
    return normalized


def clean_description(description: str | None) -> str | None:
    if description is None:
        return None
    cleaned = description.strip()
    return cleaned or None
