"""One-time auth token data access."""

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.auth.constants import (
    EMAIL_VERIFICATION_EXPIRE_HOURS,
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

    def consume(self, record: AuthToken) -> bool:
        """Mark token as consumed — returns False if already consumed."""
        if record.consumed_at is not None:
            return False
        record.consumed_at = datetime.now(UTC)
        self._session.add(record)
        self._session.flush()
        return True
