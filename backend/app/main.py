"""YurPass FastAPI application entry point."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.health import build_health_response
from app.core.logging import setup_logging
from app.modules.auth.exceptions import (
    AccountInactiveError,
    AuthTokenError,
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    RefreshTokenError,
)
from app.modules.auth.router import router as auth_router
from app.shared.responses import HealthResponse

setup_logging()
settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
)

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])


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


@app.get("/api/health", response_model=HealthResponse, tags=["health"])
def api_health() -> HealthResponse:
    """Application health probe — stable without mandatory DB/Redis."""
    return build_health_response()
