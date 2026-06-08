"""YurPass FastAPI application entry point."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.health import build_health_response
from app.core.logging import setup_logging
from app.core.rate_limit import RateLimitExceeded
from app.core.security_headers import SecurityHeadersMiddleware
from app.modules.admin.router import router as admin_router
from app.modules.auth.exceptions import (
    AccountInactiveError,
    AuthTokenError,
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    InvalidOtpError,
    OAuthGoogleError,
    OAuthStateError,
    RefreshTokenError,
)
from app.modules.auth.router import router as auth_router
from app.modules.organizations.router import router as organizations_router
from app.shared.exceptions import NotFoundError, PermissionDeniedError
from app.shared.responses import HealthResponse

setup_logging()
settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
)

app.add_middleware(SecurityHeadersMiddleware)

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(admin_router, prefix="/api/admin", tags=["admin"])
app.include_router(organizations_router, prefix="/api/organizations", tags=["organizations"])


@app.exception_handler(EmailAlreadyRegisteredError)
async def email_already_registered_handler(
    _request: Request,
    exc: EmailAlreadyRegisteredError,
) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": exc.message, "code": exc.code})


@app.exception_handler(InvalidCredentialsError)
async def invalid_credentials_handler(
    _request: Request,
    exc: InvalidCredentialsError,
) -> JSONResponse:
    return JSONResponse(status_code=401, content={"detail": exc.message, "code": exc.code})


@app.exception_handler(AccountInactiveError)
async def account_inactive_handler(
    _request: Request,
    exc: AccountInactiveError,
) -> JSONResponse:
    return JSONResponse(status_code=403, content={"detail": exc.message, "code": exc.code})


@app.exception_handler(RefreshTokenError)
async def refresh_token_error_handler(
    _request: Request,
    exc: RefreshTokenError,
) -> JSONResponse:
    return JSONResponse(status_code=401, content={"detail": exc.message, "code": exc.code})


@app.exception_handler(AuthTokenError)
async def auth_token_error_handler(
    _request: Request,
    exc: AuthTokenError,
) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": exc.message, "code": exc.code})


@app.exception_handler(InvalidOtpError)
async def invalid_otp_error_handler(
    _request: Request,
    exc: InvalidOtpError,
) -> JSONResponse:
    return JSONResponse(status_code=401, content={"detail": exc.message, "code": exc.code})


@app.exception_handler(OAuthStateError)
async def oauth_state_error_handler(
    _request: Request,
    exc: OAuthStateError,
) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": exc.message, "code": exc.code})


@app.exception_handler(OAuthGoogleError)
async def oauth_google_error_handler(
    _request: Request,
    exc: OAuthGoogleError,
) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": exc.message, "code": exc.code})


@app.exception_handler(PermissionDeniedError)
async def permission_denied_handler(
    _request: Request,
    exc: PermissionDeniedError,
) -> JSONResponse:
    return JSONResponse(status_code=403, content={"detail": exc.message, "code": exc.code})


@app.exception_handler(NotFoundError)
async def not_found_handler(
    _request: Request,
    exc: NotFoundError,
) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": exc.message, "code": exc.code})


@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(
    _request: Request,
    exc: RateLimitExceeded,
) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.get("/api/health", response_model=HealthResponse, tags=["health"])
def api_health() -> HealthResponse:
    """Application health probe — stable without mandatory DB/Redis."""
    return build_health_response()
