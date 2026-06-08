"""JWT access tokens and opaque refresh token utilities."""

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from app.core.config import Settings
from app.modules.auth.constants import GlobalRole
from app.modules.auth.models import User


class TokenError(Exception):
    """Base token validation error."""

    def __init__(self, message: str = "Invalid token") -> None:
        self.message = message
        super().__init__(message)


def generate_otp_code() -> str:
    """Generate a cryptographically secure 6-digit OTP code."""
    return f"{secrets.randbelow(1_000_000):06d}"


def generate_opaque_token() -> str:
    """Generate a cryptographically secure opaque token."""
    return secrets.token_urlsafe(48)


def generate_refresh_token() -> str:
    """Generate a cryptographically secure opaque refresh token."""
    return generate_opaque_token()


def hash_opaque_token(token: str) -> str:
    """Hash an opaque token for storage and lookup."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def hash_refresh_token(token: str) -> str:
    """Hash a refresh token for storage and lookup."""
    return hash_opaque_token(token)


def create_access_token(user: User, settings: Settings) -> tuple[str, int]:
    """Create a signed JWT access token and return (token, expires_in_seconds)."""
    expires_in = settings.access_token_expire_minutes * 60
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": str(user.id),
        "email": user.email,
        "global_role": (
            user.global_role.value
            if isinstance(user.global_role, GlobalRole)
            else user.global_role
        ),
        "token_type": "access",
        "iat": now,
        "exp": now + timedelta(seconds=expires_in),
        "jti": str(uuid.uuid4()),
    }
    token = jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return token, expires_in


def decode_access_token(token: str, settings: Settings) -> dict[str, Any]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.PyJWTError as exc:
        raise TokenError("Invalid or expired access token") from exc

    if payload.get("token_type") != "access":
        raise TokenError("Invalid token type")

    if not payload.get("sub"):
        raise TokenError("Invalid token subject")

    return payload
