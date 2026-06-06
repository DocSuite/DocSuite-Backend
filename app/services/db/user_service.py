from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import DocSuiteException
from app.core.security import get_password_hash
from app.models.role import Role
from app.models.user import User
from app.schemas.user import UserAdminCreate, UserCreate
from app.services.db.role_service import get_default_role
from app.services.email_service import send_user_created_email


def get_user_by_id(db: Session, user_id: str) -> User | None:
    return db.get(User, user_id)


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def get_user_by_password_reset_token_hash(db: Session, token_hash: str) -> User | None:
    return db.scalar(select(User).where(User.password_reset_token_hash == token_hash))


def create_user(db: Session, payload: UserCreate) -> User:
    role = get_default_role(db)
    user = User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=get_password_hash(payload.password),
        role_id=role.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_user_by_admin(db: Session, payload: UserAdminCreate) -> User:
    if get_user_by_email(db, payload.email) is not None:
        raise DocSuiteException("El correo ya esta registrado", status_code=409)

    if db.get(Role, payload.role_id) is None:
        raise DocSuiteException("Rol no encontrado", status_code=404)

    user = User(
        email=payload.email,
        full_name=payload.full_name,
        dni=payload.dni,
        hashed_password=get_password_hash(payload.dni),
        role_id=payload.role_id,
        is_active=True,
        must_change_password=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    send_user_created_email(user.full_name, user.email, payload.dni)
    return user


def list_users(db: Session) -> list[User]:
    return list(db.scalars(select(User).order_by(User.created_at.desc())).all())


def update_user_access(
    db: Session,
    user: User,
    email: str | None = None,
    full_name: str | None = None,
    dni: str | None = None,
    role_id: int | None = None,
    is_active: bool | None = None,
) -> User:
    if email is not None and email != user.email:
        if get_user_by_email(db, email) is not None:
            raise DocSuiteException("El correo ya esta registrado", status_code=409)
        user.email = email
    if full_name is not None:
        user.full_name = full_name
    if dni is not None:
        user.dni = dni
        if user.must_change_password:
            user.hashed_password = get_password_hash(dni)
    if role_id is not None:
        if db.get(Role, role_id) is None:
            raise DocSuiteException("Rol no encontrado", status_code=404)
        user.role_id = role_id
    if is_active is not None:
        user.is_active = is_active
    db.commit()
    db.refresh(user)
    return user


def update_user_profile(db: Session, user: User, full_name: str) -> User:
    user.full_name = full_name
    db.commit()
    db.refresh(user)
    return user


def set_password_reset_token(db: Session, user: User, token_hash: str, expires_at: datetime) -> User:
    user.password_reset_token_hash = token_hash
    user.password_reset_expires_at = expires_at
    db.commit()
    db.refresh(user)
    return user


def reset_user_password(db: Session, user: User, new_password: str) -> User:
    user.hashed_password = get_password_hash(new_password)
    user.password_reset_token_hash = None
    user.password_reset_expires_at = None
    user.must_change_password = False
    db.commit()
    db.refresh(user)
    return user


def password_reset_token_is_valid(user: User) -> bool:
    if user.password_reset_expires_at is None:
        return False

    expires_at = user.password_reset_expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    return expires_at > datetime.now(UTC)
