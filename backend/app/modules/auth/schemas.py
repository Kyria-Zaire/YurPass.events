"""Authentication Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.modules.auth.constants import GlobalRole, UserStatus


class RegisterRequest(BaseModel):
    """Payload for account registration."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


class LoginRequest(BaseModel):
    """Payload for email/password login."""

    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserPublic(BaseModel):
    """Public user representation — never includes secrets."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    full_name: str | None
    status: UserStatus
    global_role: GlobalRole
    email_verified_at: datetime | None
    created_at: datetime
    last_login_at: datetime | None = None


class TokenResponse(BaseModel):
    """JWT access token payload — refresh token is cookie-only."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class RegisterResponse(BaseModel):
    """Successful registration response."""

    user: UserPublic


class LoginResponse(BaseModel):
    """Successful login response with access token."""

    user: UserPublic
    tokens: TokenResponse


class RefreshResponse(BaseModel):
    """Successful refresh response."""

    tokens: TokenResponse


class LogoutResponse(BaseModel):
    """Successful logout response."""

    message: str = "logout_success"


class VerifyEmailRequest(BaseModel):
    """Payload to verify email with a one-time token."""

    token: str = Field(min_length=1, max_length=256)


class VerifyMagicLinkRequest(BaseModel):
    """Payload to complete magic link login with a one-time token."""

    token: str = Field(min_length=1, max_length=256)


class RequestMagicLinkRequest(BaseModel):
    """Payload to request a magic link login email."""

    email: EmailStr


class RequestPasswordResetRequest(BaseModel):
    """Payload to request a password reset email."""

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Payload to reset password with a one-time token."""

    token: str = Field(min_length=1, max_length=256)
    new_password: str = Field(min_length=8, max_length=128)


class MessageResponse(BaseModel):
    """Generic stable auth action response."""

    message: str


class MeResponse(BaseModel):
    """Authenticated user profile — no organization data."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    full_name: str | None
    status: UserStatus
    global_role: GlobalRole
    email_verified_at: datetime | None
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime
