"""One-time auth token data access."""

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.modules.auth.constants import (
    EMAIL_VERIFICATION_EXPIRE_HOURS,
    MAGIC_LINK_EXPIRE_MINUTES,
    OTP_LOGIN_EXPIRE_MINUTES,
    PASSWORD_RESET_EXPIRE_MINUTES,
    AuthTokenType,
)
from app.modules.auth.models import AuthToken
from app.modules.auth.tokens import hash_opaque_token


class AuthTokenRepository:
    """Repository for email verification and password reset tokens."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
        self,
        *,
        user_id: uuid.UUID,
        plain_token: str,
        token_type: AuthTokenType,
    ) -> AuthToken:
        """Persist a new hashed one-time auth token."""
        if token_type == AuthTokenType.EMAIL_VERIFICATION:
            expires_at = datetime.now(UTC) + timedelta(hours=EMAIL_VERIFICATION_EXPIRE_HOURS)
        elif token_type == AuthTokenType.MAGIC_LINK:
            expires_at = datetime.now(UTC) + timedelta(minutes=MAGIC_LINK_EXPIRE_MINUTES)
        elif token_type == AuthTokenType.OTP_LOGIN:
            expires_at = datetime.now(UTC) + timedelta(minutes=OTP_LOGIN_EXPIRE_MINUTES)
        else:
            expires_at = datetime.now(UTC) + timedelta(minutes=PASSWORD_RESET_EXPIRE_MINUTES)

        record = AuthToken(
            user_id=user_id,
            token_hash=hash_opaque_token(plain_token),
            token_type=token_type.value,
            expires_at=expires_at,
        )
        self._session.add(record)
        self._session.flush()
        self._session.refresh(record)
        return record

    def get_valid_by_plain_token(
        self,
        plain_token: str,
        token_type: AuthTokenType,
    ) -> AuthToken | None:
        """Return an active, non-expired, unconsumed token."""
        token_hash = hash_opaque_token(plain_token)
        now = datetime.now(UTC)
        statement = select(AuthToken).where(
            AuthToken.token_hash == token_hash,
            AuthToken.token_type == token_type.value,
            AuthToken.consumed_at.is_(None),
            AuthToken.expires_at > now,
        )
        return self._session.scalar(statement)

    def get_valid_for_user_by_plain_token(
        self,
        plain_token: str,
        token_type: AuthTokenType,
        user_id: uuid.UUID,
    ) -> AuthToken | None:
        """Return an active token for a specific user and plain value."""
        token_hash = hash_opaque_token(plain_token)
        now = datetime.now(UTC)
        statement = select(AuthToken).where(
            AuthToken.token_hash == token_hash,
            AuthToken.token_type == token_type.value,
            AuthToken.user_id == user_id,
            AuthToken.consumed_at.is_(None),
            AuthToken.expires_at > now,
        )
        return self._session.scalar(statement)

    def consume(self, record: AuthToken) -> bool:
        """Atomically mark token as consumed — returns False if already consumed."""
        now = datetime.now(UTC)
        statement = (
            update(AuthToken)
            .where(
                AuthToken.id == record.id,
                AuthToken.consumed_at.is_(None),
            )
            .values(consumed_at=now)
            .returning(AuthToken.consumed_at)
        )
        consumed_at = self._session.scalar(statement)
        if consumed_at is None:
            return False
        record.consumed_at = consumed_at
        return True
