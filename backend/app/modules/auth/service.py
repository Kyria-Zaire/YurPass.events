"""Authentication business logic."""

import secrets
import uuid
from typing import Any

from app.core.config import Settings
from app.modules.audit.constants import AuditAction
from app.modules.audit.service import AuditService
from app.modules.auth.auth_token_repository import AuthTokenRepository
from app.modules.auth.constants import AuthTokenType, UserStatus
from app.modules.auth.dev_outbox import record_dev_auth_link
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
from app.modules.auth.models import User
from app.modules.auth.oauth_google import GoogleOAuthClient, GoogleUserInfo
from app.modules.auth.password import google_oauth_password_hash, hash_password, verify_password
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
        google_oauth_client: GoogleOAuthClient | None = None,
        audit_service: AuditService | None = None,
    ) -> None:
        self._repository = repository
        self._refresh_repository = refresh_repository
        self._auth_token_repository = auth_token_repository
        self._settings = settings
        self._google_oauth = google_oauth_client or GoogleOAuthClient(settings)
        self._audit_service = audit_service

    def register(
        self,
        *,
        email: str,
        password: str,
        full_name: str | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
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
        self._record_audit(
            AuditAction.REGISTER_SUCCESS,
            actor_user_id=user.id,
            resource_type="user",
            resource_id=str(user.id),
            ip_address=ip_address,
            user_agent=user_agent,
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
        try:
            user = self._authenticate_credentials(email, password)
        except InvalidCredentialsError:
            self._record_audit(
                AuditAction.LOGIN_FAILED,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={"email": normalize_email(email)},
            )
            raise
        user = self._repository.update_last_login(user)
        response, plain_refresh = self._issue_session(
            user,
            user_agent=user_agent,
            ip_address=ip_address,
        )
        self._record_audit(
            AuditAction.LOGIN_SUCCESS,
            actor_user_id=user.id,
            resource_type="user",
            resource_id=str(user.id),
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return response, plain_refresh

    def refresh(
        self,
        plain_refresh: str | None,
        *,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> tuple[RefreshResponse, str]:
        """Rotate refresh token and issue a new access token."""
        if not plain_refresh:
            self._record_audit(
                AuditAction.REFRESH_FAILED,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            raise RefreshTokenError()

        record = self._refresh_repository.get_valid_by_plain_token(plain_refresh)
        if record is None:
            stolen = self._refresh_repository.get_by_plain_token_any(plain_refresh)
            if stolen is not None and stolen.revoked_at is not None:
                self._refresh_repository.revoke_all_for_session_id(stolen.session_id)
                self._record_audit(
                    AuditAction.REFRESH_REUSE_DETECTED,
                    actor_user_id=stolen.user_id,
                    resource_type="session",
                    resource_id=str(stolen.session_id),
                    ip_address=ip_address,
                    user_agent=user_agent,
                )
            self._record_audit(
                AuditAction.REFRESH_FAILED,
                actor_user_id=stolen.user_id if stolen else None,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            raise RefreshTokenError()

        user = self._repository.get_by_id(record.user_id)
        if user is None or user.status in {UserStatus.SUSPENDED, UserStatus.DELETED}:
            self._record_audit(
                AuditAction.REFRESH_FAILED,
                actor_user_id=record.user_id,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            raise RefreshTokenError()

        self._refresh_repository.mark_rotated(record)
        new_plain = generate_refresh_token()
        self._refresh_repository.create(
            user_id=user.id,
            plain_token=new_plain,
            session_id=record.session_id,
            user_agent=user_agent or record.user_agent,
            ip_address=ip_address or record.ip_address,
        )

        access_token, expires_in = create_access_token(user, self._settings)
        self._record_audit(
            AuditAction.REFRESH_SUCCESS,
            actor_user_id=user.id,
            resource_type="session",
            resource_id=str(record.session_id),
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return (
            RefreshResponse(
                tokens=TokenResponse(access_token=access_token, expires_in=expires_in),
            ),
            new_plain,
        )

    def logout(
        self,
        plain_refresh: str | None,
        *,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> LogoutResponse:
        """Revoke refresh token if present — idempotent."""
        actor_user_id = None
        if plain_refresh:
            record = self._refresh_repository.get_valid_by_plain_token(plain_refresh)
            if record is not None:
                actor_user_id = record.user_id
                self._refresh_repository.revoke(record)
        self._record_audit(
            AuditAction.LOGOUT,
            actor_user_id=actor_user_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return LogoutResponse()

    @staticmethod
    def me(user: User) -> MeResponse:
        """Map authenticated user to /me response — no organization data."""
        return MeResponse.model_validate(user)

    def request_email_verification(
        self,
        user: User,
        *,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> MessageResponse:
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
        self._record_audit(
            AuditAction.EMAIL_VERIFICATION_REQUESTED,
            actor_user_id=user.id,
            resource_type="user",
            resource_id=str(user.id),
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return MessageResponse(message="verification_email_requested")

    def verify_email(
        self,
        plain_token: str,
        *,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> MessageResponse:
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

        self._record_audit(
            AuditAction.EMAIL_VERIFIED,
            actor_user_id=user.id,
            resource_type="user",
            resource_id=str(user.id),
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return MessageResponse(message="email_verified")

    def request_password_reset(
        self,
        email: str,
        *,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> MessageResponse:
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
            self._record_audit(
                AuditAction.PASSWORD_RESET_REQUESTED,
                actor_user_id=user.id,
                resource_type="user",
                resource_id=str(user.id),
                ip_address=ip_address,
                user_agent=user_agent,
            )
        return MessageResponse(message="password_reset_requested")

    def reset_password(
        self,
        plain_token: str,
        new_password: str,
        *,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> MessageResponse:
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
        self._record_audit(
            AuditAction.PASSWORD_RESET_SUCCESS,
            actor_user_id=user.id,
            resource_type="user",
            resource_id=str(user.id),
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return MessageResponse(message="password_reset_success")

    def request_magic_link(
        self,
        email: str,
        *,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> MessageResponse:
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
            self._record_audit(
                AuditAction.MAGIC_LINK_REQUESTED,
                actor_user_id=user.id,
                resource_type="user",
                resource_id=str(user.id),
                ip_address=ip_address,
                user_agent=user_agent,
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
        response, plain_refresh = self._issue_session(
            user,
            user_agent=user_agent,
            ip_address=ip_address,
        )
        self._record_audit(
            AuditAction.MAGIC_LINK_SUCCESS,
            actor_user_id=user.id,
            resource_type="user",
            resource_id=str(user.id),
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return response, plain_refresh

    def request_otp(
        self,
        email: str,
        *,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> MessageResponse:
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
            self._record_audit(
                AuditAction.OTP_REQUESTED,
                actor_user_id=user.id,
                resource_type="user",
                resource_id=str(user.id),
                ip_address=ip_address,
                user_agent=user_agent,
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
        response, plain_refresh = self._issue_session(
            user,
            user_agent=user_agent,
            ip_address=ip_address,
        )
        self._record_audit(
            AuditAction.OTP_SUCCESS,
            actor_user_id=user.id,
            resource_type="user",
            resource_id=str(user.id),
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return response, plain_refresh

    def start_google_oauth(self) -> tuple[str, str]:
        """Build Google authorization redirect URL and CSRF state."""
        state = generate_opaque_token()
        redirect_url = self._google_oauth.build_authorization_url(state)
        return redirect_url, state

    def complete_google_oauth(
        self,
        *,
        code: str,
        state: str | None,
        cookie_state: str | None,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> tuple[LoginResponse, str]:
        """Validate OAuth state, authenticate with Google, and issue session."""
        if not state or not cookie_state or not secrets.compare_digest(state, cookie_state):
            self._record_audit(
                AuditAction.GOOGLE_OAUTH_FAILED,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            raise OAuthStateError()

        try:
            google_user = self._google_oauth.authenticate_with_code(code)
            user = self._resolve_google_user(google_user)
        except OAuthGoogleError:
            self._record_audit(
                AuditAction.GOOGLE_OAUTH_FAILED,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            raise

        if user.status in {UserStatus.SUSPENDED, UserStatus.DELETED}:
            self._record_audit(
                AuditAction.GOOGLE_OAUTH_FAILED,
                actor_user_id=user.id,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            raise AccountInactiveError(status=user.status.value)

        user = self._repository.update_last_login(user)
        response, plain_refresh = self._issue_session(
            user,
            user_agent=user_agent,
            ip_address=ip_address,
        )
        self._record_audit(
            AuditAction.GOOGLE_OAUTH_SUCCESS,
            actor_user_id=user.id,
            resource_type="user",
            resource_id=str(user.id),
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return response, plain_refresh

    def _resolve_google_user(self, google_user: GoogleUserInfo) -> User:
        """Find, link, or create a user from Google userinfo."""
        user = self._repository.get_by_google_sub(google_user.sub)
        if user is not None:
            return user

        user = self._repository.get_by_email(google_user.email)
        if user is not None:
            if user.google_sub is not None and user.google_sub != google_user.sub:
                raise OAuthGoogleError("Google account conflict")
            return self._repository.link_google_account(
                user,
                google_sub=google_user.sub,
                full_name=google_user.name,
                avatar_url=google_user.picture,
            )

        return self._repository.create_google_user(
            email=google_user.email,
            google_sub=google_user.sub,
            password_hash=google_oauth_password_hash(),
            full_name=google_user.name,
            avatar_url=google_user.picture,
        )

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

    def _record_audit(
        self,
        action: AuditAction,
        *,
        actor_user_id: uuid.UUID | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Record audit event when audit service is configured."""
        if self._audit_service is None:
            return
        self._audit_service.record(
            action.value,
            actor_user_id=actor_user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata,
        )
