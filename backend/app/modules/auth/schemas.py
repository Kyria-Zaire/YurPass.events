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


class RegisterResponse(BaseModel):
    """Successful registration response."""

    user: UserPublic


class LoginResponse(BaseModel):
    """Successful login response — tokens reserved for TICKET-006B."""

    user: UserPublic
    tokens: None = None
