"""Authentication HTTP routes."""

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.modules.auth.auth_token_repository import AuthTokenRepository
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
    MessageResponse,
    RefreshResponse,
    RegisterRequest,
    RegisterResponse,
    RequestMagicLinkRequest,
    RequestPasswordResetRequest,
    ResetPasswordRequest,
    VerifyEmailRequest,
    VerifyMagicLinkRequest,
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
        AuthTokenRepository(db),
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


@router.post("/request-email-verification", response_model=MessageResponse)
def request_email_verification(
    current_user: User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    """Request a one-time email verification token."""
    return service.request_email_verification(current_user)


@router.post("/verify-email", response_model=MessageResponse)
def verify_email(
    payload: VerifyEmailRequest,
    service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    """Verify email using a one-time token."""
    return service.verify_email(payload.token)


@router.post("/request-password-reset", response_model=MessageResponse)
def request_password_reset(
    payload: RequestPasswordResetRequest,
    service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    """Request a password reset — stable response for unknown emails."""
    return service.request_password_reset(str(payload.email))


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(
    payload: ResetPasswordRequest,
    service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    """Reset password using a one-time token."""
    return service.reset_password(payload.token, payload.new_password)


@router.post("/request-magic-link", response_model=MessageResponse)
def request_magic_link(
    payload: RequestMagicLinkRequest,
    service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    """Request a magic link — stable response for unknown emails."""
    return service.request_magic_link(str(payload.email))


@router.post("/verify-magic-link", response_model=LoginResponse)
def verify_magic_link(
    payload: VerifyMagicLinkRequest,
    request: Request,
    response: Response,
    service: AuthService = Depends(get_auth_service),
    settings: Settings = Depends(get_settings),
) -> LoginResponse:
    """Complete passwordless login using a one-time magic link token."""
    login_response, plain_refresh = service.verify_magic_link(
        payload.token,
        user_agent=request.headers.get("user-agent"),
        ip_address=_client_ip(request),
    )
    set_refresh_cookie(response, plain_refresh, settings)
    return login_response
