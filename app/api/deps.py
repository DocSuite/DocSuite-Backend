from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import UnauthorizedException
from app.core.jwt import decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.services.db.user_service import get_user_by_id

settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_v1_prefix}/auth/login")

DbSession = Annotated[Session, Depends(get_db)]
TokenDep = Annotated[str, Depends(oauth2_scheme)]


def get_current_user(db: DbSession, token: TokenDep) -> User:
    user_id = decode_access_token(token)
    if user_id is None:
        raise UnauthorizedException()

    user = get_user_by_id(db, user_id)
    if user is None or not user.is_active:
        raise UnauthorizedException()

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
