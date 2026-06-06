import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import CurrentUser, DbSession, require_permission
from app.core.config import get_settings
from app.core.exceptions import DocSuiteException, UnauthorizedException
from app.core.jwt import create_access_token
from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.schemas.auth import AuthResponse, ChangePasswordRequest, ForgotPasswordRequest, MessageResponse, ResetPasswordRequest, Token
from app.schemas.user import UserCreate, UserProfileUpdate, UserRead
from app.services.db.audit_service import create_audit_event
from app.services.db.role_service import get_user_permissions
from app.services.db.user_service import (
    create_user,
    get_user_by_email,
    get_user_by_password_reset_token_hash,
    password_reset_token_is_valid,
    reset_user_password,
    set_password_reset_token,
    update_user_profile,
)
from app.services.email_service import send_password_reset_email

router = APIRouter()
ProfileEditor = Annotated[User, Depends(require_permission("/profile", "update"))]


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: DbSession) -> AuthResponse:
    if get_user_by_email(db, payload.email) is not None:
        raise DocSuiteException("El correo ya esta registrado", status.HTTP_409_CONFLICT)

    user = create_user(db, payload)
    create_audit_event(db, user.id, "Usuario registrado", "Auth", detail=user.email)
    token = Token(access_token=create_access_token(user.id))
    return AuthResponse(user=UserRead.model_validate(user), token=token)


@router.post("/login", response_model=Token)
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: DbSession) -> Token:
    user = get_user_by_email(db, form_data.username)
    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise UnauthorizedException()

    create_audit_event(db, user.id, "Inicio de sesion", "Auth", detail=user.email)
    return Token(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserRead)
def read_me(db: DbSession, current_user: CurrentUser) -> UserRead:
    data = UserRead.model_validate(current_user)
    data.permissions = get_user_permissions(db, current_user)
    return data


@router.patch("/me", response_model=UserRead)
def update_me(
    payload: UserProfileUpdate,
    db: DbSession,
    current_user: ProfileEditor,
) -> UserRead:
    user = update_user_profile(db, current_user, payload.full_name)
    create_audit_event(db, user.id, "Perfil actualizado", "Auth", detail=user.email)
    data = UserRead.model_validate(user)
    data.permissions = get_user_permissions(db, user)
    return data


@router.post("/change-password", response_model=UserRead)
def change_password(
    payload: ChangePasswordRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> UserRead:
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise UnauthorizedException("La contrasena actual no es correcta")

    if payload.current_password == payload.new_password:
        raise DocSuiteException("La nueva contrasena debe ser diferente")

    current_user.hashed_password = get_password_hash(payload.new_password)
    current_user.must_change_password = False
    db.commit()
    db.refresh(current_user)
    create_audit_event(db, current_user.id, "Contrasena actualizada", "Auth", detail=current_user.email)
    data = UserRead.model_validate(current_user)
    data.permissions = get_user_permissions(db, current_user)
    return data


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(payload: ForgotPasswordRequest, db: DbSession) -> MessageResponse:
    user = get_user_by_email(db, payload.email.strip().lower())
    if user is not None and user.is_active:
        settings = get_settings()
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(UTC) + timedelta(minutes=settings.password_reset_token_expire_minutes)
        set_password_reset_token(db, user, _hash_reset_token(token), expires_at)
        reset_url = f"{settings.frontend_url.rstrip('/')}/reset-password?token={token}"
        send_password_reset_email(user.full_name, user.email, reset_url)
        create_audit_event(db, user.id, "Restablecimiento solicitado", "Auth", detail=user.email)

    return MessageResponse(message="Si el correo existe, enviaremos instrucciones para restablecer la contrasena.")


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(payload: ResetPasswordRequest, db: DbSession) -> MessageResponse:
    user = get_user_by_password_reset_token_hash(db, _hash_reset_token(payload.token))
    if user is None or not password_reset_token_is_valid(user):
        raise DocSuiteException("El enlace de restablecimiento no es valido o ya vencio", status_code=400)

    reset_user_password(db, user, payload.new_password)
    create_audit_event(db, user.id, "Contrasena restablecida", "Auth", detail=user.email)
    return MessageResponse(message="Contrasena restablecida. Inicia sesion con tu nueva contrasena.")


def _hash_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
