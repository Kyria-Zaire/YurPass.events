"""Refresh token data access."""

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.modules.auth.models import RefreshToken
from app.modules.auth.tokens import hash_refresh_token


class RefreshTokenRepository:
    """Repository for refresh token persistence and rotation."""

    def __init__(self, session: Session, settings: Settings) -> None:
        self._session = session
        self._settings = settings

    def create(
        self,
        *,
        user_id: uuid.UUID,
        plain_token: str,
        session_id: uuid.UUID,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> RefreshToken:
        """Persist a new hashed refresh token."""
        expires_at = datetime.now(UTC) + timedelta(days=self._settings.refresh_token_expire_days)
        record = RefreshToken(
            user_id=user_id,
            token_hash=hash_refresh_token(plain_token),
            session_id=session_id,
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=ip_address,
        )
        self._session.add(record)
        self._session.flush()
        self._session.refresh(record)
        return record

    def get_valid_by_plain_token(self, plain_token: str) -> RefreshToken | None:
        """Return an active, non-expired refresh token matching the plain value."""
        token_hash = hash_refresh_token(plain_token)
        now = datetime.now(UTC)
        statement = select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > now,
        )
        return self._session.scalar(statement)

    def mark_rotated(self, record: RefreshToken) -> None:
        """Mark a refresh token as rotated and revoked."""
        now = datetime.now(UTC)
        record.rotated_at = now
        record.revoked_at = now
        self._session.add(record)
        self._session.flush()

    def revoke(self, record: RefreshToken) -> None:
        """Revoke a refresh token."""
        record.revoked_at = datetime.now(UTC)
        self._session.add(record)
        self._session.flush()
