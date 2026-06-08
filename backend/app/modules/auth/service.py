"""Authentication business logic."""

import uuid

from app.core.config import Settings
from app.modules.auth.auth_token_repository import AuthTokenRepository
from app.modules.auth.constants import AuthTokenType, UserStatus
from app.modules.auth.dev_outbox import record_dev_auth_link
from app.modules.auth.exceptions import (
    AccountInactiveError,
    AuthTokenError,
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    InvalidOtpError,
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
    MessageResponse,
    RefreshResponse,
    RegisterResponse,
    TokenResponse,
    UserPublic,
)
from app.modules.auth.tokens import (
    create_access_token,
    generate_opaque_token,
    generate_otp_code,
    generate_refresh_token,
)


def normalize_email(email: str) -> str:
    """Normalize email for storage and lookup."""
    return email.strip().lower()


class AuthService:
    """Service layer for Authentication module."""

    def __init__(
        self,
        repository: AuthRepository,
        refresh_repository: RefreshTokenRepository,
        auth_token_repository: AuthTokenRepository,
        settings: Settings,
    ) -> None:
        self._repository = repository
        self._refresh_repository = refresh_repository
        self._auth_token_repository = auth_token_repository
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
        return self._issue_session(user, user_agent=user_agent, ip_address=ip_address)

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

    def request_email_verification(self, user: User) -> MessageResponse:
        """Issue a one-time email verification token."""
        if user.email_verified_at is not None:
            return MessageResponse(message="verification_email_requested")

        plain_token = generate_opaque_token()
        self._auth_token_repository.create(
            user_id=user.id,
            plain_token=plain_token,
            token_type=AuthTokenType.EMAIL_VERIFICATION,
        )
        record_dev_auth_link(
            settings=self._settings,
            kind="email_verification",
            email=user.email,
            plain_token=plain_token,
            path="/api/auth/verify-email",
        )
        return MessageResponse(message="verification_email_requested")

    def verify_email(self, plain_token: str) -> MessageResponse:
        """Consume verification token and mark email as verified."""
        record = self._auth_token_repository.get_valid_by_plain_token(
            plain_token,
            AuthTokenType.EMAIL_VERIFICATION,
        )
        if record is None:
            raise AuthTokenError()

        user = self._repository.get_by_id(record.user_id)
        if user is None:
            raise AuthTokenError()

        if not self._auth_token_repository.consume(record):
            raise AuthTokenError()

        if user.email_verified_at is None:
            self._repository.mark_email_verified(user)

        return MessageResponse(message="email_verified")

    def request_password_reset(self, email: str) -> MessageResponse:
        """Issue password reset token — stable response regardless of email existence."""
        normalized_email = normalize_email(email)
        user = self._repository.get_by_email(normalized_email)
        if user is not None:
            plain_token = generate_opaque_token()
            self._auth_token_repository.create(
                user_id=user.id,
                plain_token=plain_token,
                token_type=AuthTokenType.PASSWORD_RESET,
            )
            record_dev_auth_link(
                settings=self._settings,
                kind="password_reset",
                email=user.email,
                plain_token=plain_token,
                path="/api/auth/reset-password",
            )
        return MessageResponse(message="password_reset_requested")

    def reset_password(self, plain_token: str, new_password: str) -> MessageResponse:
        """Consume reset token, update password, revoke active refresh sessions."""
        record = self._auth_token_repository.get_valid_by_plain_token(
            plain_token,
            AuthTokenType.PASSWORD_RESET,
        )
        if record is None:
            raise AuthTokenError()

        user = self._repository.get_by_id(record.user_id)
        if user is None:
            raise AuthTokenError()

        if not self._auth_token_repository.consume(record):
            raise AuthTokenError()

        self._repository.update_password_hash(user, hash_password(new_password))
        self._refresh_repository.revoke_all_active_for_user(user.id)
        return MessageResponse(message="password_reset_success")

    def request_magic_link(self, email: str) -> MessageResponse:
        """Issue magic link token — stable response regardless of email existence."""
        normalized_email = normalize_email(email)
        user = self._repository.get_by_email(normalized_email)
        if user is not None and user.status not in {UserStatus.SUSPENDED, UserStatus.DELETED}:
            plain_token = generate_opaque_token()
            self._auth_token_repository.create(
                user_id=user.id,
                plain_token=plain_token,
                token_type=AuthTokenType.MAGIC_LINK,
            )
            record_dev_auth_link(
                settings=self._settings,
                kind="magic_link",
                email=user.email,
                plain_token=plain_token,
                path="/api/auth/verify-magic-link",
            )
        return MessageResponse(message="magic_link_requested")

    def verify_magic_link(
        self,
        plain_token: str,
        *,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> tuple[LoginResponse, str]:
        """Consume magic link token and issue a full login session."""
        record = self._auth_token_repository.get_valid_by_plain_token(
            plain_token,
            AuthTokenType.MAGIC_LINK,
        )
        if record is None:
            raise AuthTokenError()

        user = self._repository.get_by_id(record.user_id)
        if user is None:
            raise AuthTokenError()

        if not self._auth_token_repository.consume(record):
            raise AuthTokenError()

        if user.status in {UserStatus.SUSPENDED, UserStatus.DELETED}:
            raise AccountInactiveError(status=user.status.value)

        user = self._repository.update_last_login(user)
        return self._issue_session(user, user_agent=user_agent, ip_address=ip_address)

    def request_otp(self, email: str) -> MessageResponse:
        """Issue OTP login code — stable response regardless of email existence."""
        normalized_email = normalize_email(email)
        user = self._repository.get_by_email(normalized_email)
        if user is not None and user.status not in {UserStatus.SUSPENDED, UserStatus.DELETED}:
            otp_code = generate_otp_code()
            self._auth_token_repository.create(
                user_id=user.id,
                plain_token=otp_code,
                token_type=AuthTokenType.OTP_LOGIN,
            )
            record_dev_auth_link(
                settings=self._settings,
                kind="otp_login",
                email=user.email,
                plain_token=otp_code,
                path="/api/auth/verify-otp",
            )
        return MessageResponse(message="otp_requested")

    def verify_otp(
        self,
        email: str,
        code: str,
        *,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> tuple[LoginResponse, str]:
        """Consume OTP code and issue a full login session."""
        normalized_email = normalize_email(email)
        user = self._repository.get_by_email(normalized_email)
        if user is None or user.status in {UserStatus.SUSPENDED, UserStatus.DELETED}:
            raise InvalidOtpError()

        record = self._auth_token_repository.get_valid_for_user_by_plain_token(
            code,
            AuthTokenType.OTP_LOGIN,
            user.id,
        )
        if record is None:
            raise InvalidOtpError()

        if not self._auth_token_repository.consume(record):
            raise InvalidOtpError()

        user = self._repository.update_last_login(user)
        return self._issue_session(user, user_agent=user_agent, ip_address=ip_address)

    def _issue_session(
        self,
        user: User,
        *,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> tuple[LoginResponse, str]:
        """Create JWT access token and hashed refresh session."""
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
