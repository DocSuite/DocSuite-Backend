from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import CurrentUser, DbSession
from app.core.exceptions import DocSuiteException, UnauthorizedException
from app.core.jwt import create_access_token
from app.core.security import verify_password
from app.schemas.auth import AuthResponse, Token
from app.schemas.user import UserCreate, UserRead
from app.services.db.audit_service import create_audit_event
from app.services.db.user_service import create_user, get_user_by_email

router = APIRouter()


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
def read_me(current_user: CurrentUser) -> UserRead:
    return UserRead.model_validate(current_user)
