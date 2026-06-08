"""FastAPI authentication dependencies."""

from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.modules.auth.constants import UserStatus
from app.modules.auth.exceptions import InvalidCredentialsError
from app.modules.auth.models import User
from app.modules.auth.repository import AuthRepository
from app.modules.auth.tokens import TokenError, decode_access_token

_bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> User:
    """Extract, verify JWT access token and load the authenticated user."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise InvalidCredentialsError()

    try:
        payload = decode_access_token(credentials.credentials, settings)
        user_id = UUID(str(payload["sub"]))
    except (TokenError, ValueError) as exc:
        raise InvalidCredentialsError() from exc

    user = AuthRepository(db).get_by_id(user_id)
    if user is None:
        raise InvalidCredentialsError()

    if user.status in {UserStatus.SUSPENDED, UserStatus.DELETED}:
        raise InvalidCredentialsError()

    return user
