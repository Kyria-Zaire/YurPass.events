"""Refresh token cookie helpers."""

from fastapi import Response

from app.core.config import Settings


def set_refresh_cookie(response: Response, refresh_token: str, settings: Settings) -> None:
    """Set the HttpOnly refresh token cookie."""
    max_age = settings.refresh_token_expire_days * 24 * 60 * 60
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=refresh_token,
        max_age=max_age,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        path="/api/auth",
    )


def clear_refresh_cookie(response: Response, settings: Settings) -> None:
    """Remove the refresh token cookie."""
    response.delete_cookie(
        key=settings.refresh_cookie_name,
        path="/api/auth",
    )
