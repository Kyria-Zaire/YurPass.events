"""Authentication HTTP routes."""

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.modules.auth.cookies import clear_refresh_cookie, set_refresh_cookie
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.auth.refresh_repository import RefreshTokenRepository
from app.modules.auth.repository import AuthRepository
from app.modules.auth.schemas import (
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    MeResponse,
    RefreshResponse,
    RegisterRequest,
    RegisterResponse,
)
from app.modules.auth.service import AuthService

router = APIRouter()


def get_auth_service(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> AuthService:
    """Provide AuthService with database session and settings."""
    return AuthService(
        AuthRepository(db),
        RefreshTokenRepository(db, settings),
        settings,
    )


def _client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()[:64]
    if request.client:
        return request.client.host[:64]
    return None


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    payload: RegisterRequest,
    service: AuthService = Depends(get_auth_service),
) -> RegisterResponse:
    """Create a new account with email and password."""
    return service.register(
        email=str(payload.email),
        password=payload.password,
        full_name=payload.full_name,
    )


@router.post("/login", response_model=LoginResponse)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    service: AuthService = Depends(get_auth_service),
    settings: Settings = Depends(get_settings),
) -> LoginResponse:
    """Authenticate with email and password."""
    login_response, plain_refresh = service.login(
        email=str(payload.email),
        password=payload.password,
        user_agent=request.headers.get("user-agent"),
        ip_address=_client_ip(request),
    )
    set_refresh_cookie(response, plain_refresh, settings)
    return login_response


@router.post("/refresh", response_model=RefreshResponse)
def refresh_session(
    request: Request,
    response: Response,
    service: AuthService = Depends(get_auth_service),
    settings: Settings = Depends(get_settings),
) -> RefreshResponse:
    """Rotate refresh token and issue a new access token."""
    plain_refresh = request.cookies.get(settings.refresh_cookie_name)
    refresh_response, new_plain = service.refresh(plain_refresh)
    set_refresh_cookie(response, new_plain, settings)
    return refresh_response


@router.post("/logout", response_model=LogoutResponse)
def logout(
    request: Request,
    response: Response,
    service: AuthService = Depends(get_auth_service),
    settings: Settings = Depends(get_settings),
) -> LogoutResponse:
    """Revoke refresh session and clear cookie."""
    plain_refresh = request.cookies.get(settings.refresh_cookie_name)
    logout_response = service.logout(plain_refresh)
    clear_refresh_cookie(response, settings)
    return logout_response


@router.get("/me", response_model=MeResponse)
def me(current_user: User = Depends(get_current_user)) -> MeResponse:
    """Return the authenticated user profile."""
    return AuthService.me(current_user)
