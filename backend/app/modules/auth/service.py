"""Authentication business logic."""

import uuid

from app.core.config import Settings
from app.modules.auth.constants import UserStatus
from app.modules.auth.exceptions import (
    AccountInactiveError,
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    RefreshTokenError,
)
from app.modules.auth.models import User
from app.modules.auth.password import hash_password, verify_password
from app.modules.auth.refresh_repository import RefreshTokenRepository
from app.modules.auth.repository import AuthRepository
from app.modules.auth.schemas import (
    LoginResponse,
    LogoutResponse,
    MeResponse,
    RefreshResponse,
    RegisterResponse,
    TokenResponse,
    UserPublic,
)
from app.modules.auth.tokens import create_access_token, generate_refresh_token


def normalize_email(email: str) -> str:
    """Normalize email for storage and lookup."""
    return email.strip().lower()


class AuthService:
    """Service layer for Authentication module."""

    def __init__(
        self,
        repository: AuthRepository,
        refresh_repository: RefreshTokenRepository,
        settings: Settings,
    ) -> None:
        self._repository = repository
        self._refresh_repository = refresh_repository
        self._settings = settings

    def register(
        self,
        *,
        email: str,
        password: str,
        full_name: str | None,
    ) -> RegisterResponse:
        """Register a new user with email and password."""
        normalized_email = normalize_email(email)
        if self._repository.get_by_email(normalized_email) is not None:
            raise EmailAlreadyRegisteredError()

        user = self._repository.create_user(
            email=normalized_email,
            password_hash=hash_password(password),
            full_name=full_name,
        )
        return RegisterResponse(user=UserPublic.model_validate(user))

    def login(
        self,
        *,
        email: str,
        password: str,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> tuple[LoginResponse, str]:
        """Authenticate and issue access + refresh session."""
        user = self._authenticate_credentials(email, password)
        user = self._repository.update_last_login(user)

        access_token, expires_in = create_access_token(user, self._settings)
        plain_refresh = generate_refresh_token()
        session_id = uuid.uuid4()
        self._refresh_repository.create(
            user_id=user.id,
            plain_token=plain_refresh,
            session_id=session_id,
            user_agent=user_agent,
            ip_address=ip_address,
        )

        response = LoginResponse(
            user=UserPublic.model_validate(user),
            tokens=TokenResponse(
                access_token=access_token,
                expires_in=expires_in,
            ),
        )
        return response, plain_refresh

    def refresh(self, plain_refresh: str | None) -> tuple[RefreshResponse, str]:
        """Rotate refresh token and issue a new access token."""
        if not plain_refresh:
            raise RefreshTokenError()

        record = self._refresh_repository.get_valid_by_plain_token(plain_refresh)
        if record is None:
            raise RefreshTokenError()

        user = self._repository.get_by_id(record.user_id)
        if user is None or user.status in {UserStatus.SUSPENDED, UserStatus.DELETED}:
            raise RefreshTokenError()

        self._refresh_repository.mark_rotated(record)
        new_plain = generate_refresh_token()
        self._refresh_repository.create(
            user_id=user.id,
            plain_token=new_plain,
            session_id=record.session_id,
            user_agent=record.user_agent,
            ip_address=record.ip_address,
        )

        access_token, expires_in = create_access_token(user, self._settings)
        return (
            RefreshResponse(
                tokens=TokenResponse(access_token=access_token, expires_in=expires_in),
            ),
            new_plain,
        )

    def logout(self, plain_refresh: str | None) -> LogoutResponse:
        """Revoke refresh token if present — idempotent."""
        if plain_refresh:
            record = self._refresh_repository.get_valid_by_plain_token(plain_refresh)
            if record is not None:
                self._refresh_repository.revoke(record)
        return LogoutResponse()

    @staticmethod
    def me(user: User) -> MeResponse:
        """Map authenticated user to /me response — no organization data."""
        return MeResponse.model_validate(user)

    def _authenticate_credentials(self, email: str, password: str) -> User:
        """Validate email/password and return the user."""
        normalized_email = normalize_email(email)
        user = self._repository.get_by_email(normalized_email)

        if user is None or not verify_password(password, user.password_hash):
            raise InvalidCredentialsError()

        if user.status in {UserStatus.SUSPENDED, UserStatus.DELETED}:
            raise AccountInactiveError(status=user.status.value)

        return user

    @staticmethod
    def to_public(user: User) -> UserPublic:
        """Map a User entity to a public schema."""
        return UserPublic.model_validate(user)
