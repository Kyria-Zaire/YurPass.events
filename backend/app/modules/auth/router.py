"""Authentication HTTP routes."""

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.rate_limit import check_rate_limit
from app.db.session import get_db
from app.modules.audit.repository import AuditRepository
from app.modules.audit.service import AuditService
from app.modules.auth.auth_token_repository import AuthTokenRepository
from app.modules.auth.cookies import (
    clear_oauth_state_cookie,
    clear_refresh_cookie,
    set_oauth_state_cookie,
    set_refresh_cookie,
)
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
    RequestOtpRequest,
    RequestPasswordResetRequest,
    ResetPasswordRequest,
    VerifyEmailRequest,
    VerifyMagicLinkRequest,
    VerifyOtpRequest,
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
        audit_service=AuditService(AuditRepository(db)),
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
    request: Request,
    service: AuthService = Depends(get_auth_service),
    settings: Settings = Depends(get_settings),
) -> RegisterResponse:
    """Create a new account with email and password."""
    check_rate_limit(request, limit=10, window_seconds=60, settings=settings)
    return service.register(
        email=str(payload.email),
        password=payload.password,
        full_name=payload.full_name,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
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
    check_rate_limit(
        request,
        limit=10,
        window_seconds=60,
        email=str(payload.email),
        settings=settings,
    )
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
    check_rate_limit(request, limit=30, window_seconds=60, settings=settings)
    plain_refresh = request.cookies.get(settings.refresh_cookie_name)
    refresh_response, new_plain = service.refresh(
        plain_refresh,
        user_agent=request.headers.get("user-agent"),
        ip_address=_client_ip(request),
    )
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
    logout_response = service.logout(
        plain_refresh,
        user_agent=request.headers.get("user-agent"),
        ip_address=_client_ip(request),
    )
    clear_refresh_cookie(response, settings)
    return logout_response


@router.get("/me", response_model=MeResponse)
def me(current_user: User = Depends(get_current_user)) -> MeResponse:
    """Return the authenticated user profile."""
    return AuthService.me(current_user)


@router.post("/request-email-verification", response_model=MessageResponse)
def request_email_verification(
    request: Request,
    current_user: User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
    settings: Settings = Depends(get_settings),
) -> MessageResponse:
    """Request a one-time email verification token."""
    check_rate_limit(request, limit=5, window_seconds=60, settings=settings)
    return service.request_email_verification(
        current_user,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )


@router.post("/verify-email", response_model=MessageResponse)
def verify_email(
    payload: VerifyEmailRequest,
    request: Request,
    service: AuthService = Depends(get_auth_service),
    settings: Settings = Depends(get_settings),
) -> MessageResponse:
    """Verify email using a one-time token."""
    check_rate_limit(request, limit=10, window_seconds=60, settings=settings)
    return service.verify_email(
        payload.token,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )


@router.post("/request-password-reset", response_model=MessageResponse)
def request_password_reset(
    payload: RequestPasswordResetRequest,
    request: Request,
    service: AuthService = Depends(get_auth_service),
    settings: Settings = Depends(get_settings),
) -> MessageResponse:
    """Request a password reset — stable response for unknown emails."""
    check_rate_limit(
        request,
        limit=5,
        window_seconds=60,
        email=str(payload.email),
        settings=settings,
    )
    return service.request_password_reset(
        str(payload.email),
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(
    payload: ResetPasswordRequest,
    request: Request,
    service: AuthService = Depends(get_auth_service),
    settings: Settings = Depends(get_settings),
) -> MessageResponse:
    """Reset password using a one-time token."""
    check_rate_limit(request, limit=10, window_seconds=60, settings=settings)
    return service.reset_password(
        payload.token,
        payload.new_password,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )


@router.post("/request-magic-link", response_model=MessageResponse)
def request_magic_link(
    payload: RequestMagicLinkRequest,
    request: Request,
    service: AuthService = Depends(get_auth_service),
    settings: Settings = Depends(get_settings),
) -> MessageResponse:
    """Request a magic link — stable response for unknown emails."""
    check_rate_limit(
        request,
        limit=5,
        window_seconds=60,
        email=str(payload.email),
        settings=settings,
    )
    return service.request_magic_link(
        str(payload.email),
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )


@router.post("/verify-magic-link", response_model=LoginResponse)
def verify_magic_link(
    payload: VerifyMagicLinkRequest,
    request: Request,
    response: Response,
    service: AuthService = Depends(get_auth_service),
    settings: Settings = Depends(get_settings),
) -> LoginResponse:
    """Complete passwordless login using a one-time magic link token."""
    check_rate_limit(request, limit=10, window_seconds=60, settings=settings)
    login_response, plain_refresh = service.verify_magic_link(
        payload.token,
        user_agent=request.headers.get("user-agent"),
        ip_address=_client_ip(request),
    )
    set_refresh_cookie(response, plain_refresh, settings)
    return login_response


@router.post("/request-otp", response_model=MessageResponse)
def request_otp(
    payload: RequestOtpRequest,
    request: Request,
    service: AuthService = Depends(get_auth_service),
    settings: Settings = Depends(get_settings),
) -> MessageResponse:
    """Request an email OTP login code — stable response for unknown emails."""
    check_rate_limit(
        request,
        limit=5,
        window_seconds=60,
        email=str(payload.email),
        settings=settings,
    )
    return service.request_otp(
        str(payload.email),
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )


@router.post("/verify-otp", response_model=LoginResponse)
def verify_otp(
    payload: VerifyOtpRequest,
    request: Request,
    response: Response,
    service: AuthService = Depends(get_auth_service),
    settings: Settings = Depends(get_settings),
) -> LoginResponse:
    """Complete passwordless login using an email OTP code."""
    check_rate_limit(
        request,
        limit=10,
        window_seconds=60,
        email=str(payload.email),
        settings=settings,
    )
    login_response, plain_refresh = service.verify_otp(
        str(payload.email),
        payload.code,
        user_agent=request.headers.get("user-agent"),
        ip_address=_client_ip(request),
    )
    set_refresh_cookie(response, plain_refresh, settings)
    return login_response


@router.get("/google")
def google_oauth_start(
    service: AuthService = Depends(get_auth_service),
    settings: Settings = Depends(get_settings),
) -> RedirectResponse:
    """Start Google OAuth Authorization Code Flow."""
    redirect_url, state = service.start_google_oauth()
    redirect = RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)
    set_oauth_state_cookie(redirect, state, settings)
    return redirect


@router.get("/google/callback", response_model=LoginResponse)
def google_oauth_callback(
    code: str,
    state: str,
    request: Request,
    response: Response,
    service: AuthService = Depends(get_auth_service),
    settings: Settings = Depends(get_settings),
) -> LoginResponse:
    """Complete Google OAuth and issue application session."""
    check_rate_limit(request, limit=20, window_seconds=60, settings=settings)
    cookie_state = request.cookies.get(settings.oauth_state_cookie_name)
    login_response, plain_refresh = service.complete_google_oauth(
        code=code,
        state=state,
        cookie_state=cookie_state,
        user_agent=request.headers.get("user-agent"),
        ip_address=_client_ip(request),
    )
    clear_oauth_state_cookie(response, settings)
    set_refresh_cookie(response, plain_refresh, settings)
    return login_response
