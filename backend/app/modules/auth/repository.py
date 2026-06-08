"""Authentication data access."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.auth.constants import AuthProvider, GlobalRole, UserStatus
from app.modules.auth.models import User


class AuthRepository:
    """Repository layer for Authentication module."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_email(self, email: str) -> User | None:
        """Return a user by normalized email, if any."""
        statement = select(User).where(User.email == email)
        return self._session.scalar(statement)

    def get_by_id(self, user_id: UUID) -> User | None:
        """Return a user by primary key, if any."""
        statement = select(User).where(User.id == user_id)
        return self._session.scalar(statement)

    def get_by_google_sub(self, google_sub: str) -> User | None:
        """Return a user linked to a Google subject, if any."""
        statement = select(User).where(User.google_sub == google_sub)
        return self._session.scalar(statement)

    def create_user(
        self,
        *,
        email: str,
        password_hash: str,
        full_name: str | None,
    ) -> User:
        """Persist a new user account."""
        user = User(
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            status=UserStatus.PENDING_VERIFICATION,
            global_role=GlobalRole.USER,
        )
        self._session.add(user)
        self._session.flush()
        self._session.refresh(user)
        return user

    def update_last_login(self, user: User) -> User:
        """Update last login timestamp."""
        user.last_login_at = datetime.now(UTC)
        self._session.add(user)
        self._session.flush()
        self._session.refresh(user)
        return user

    def mark_email_verified(self, user: User) -> User:
        """Set email_verified_at and activate account when pending verification."""
        user.email_verified_at = datetime.now(UTC)
        if user.status == UserStatus.PENDING_VERIFICATION:
            user.status = UserStatus.ACTIVE
        self._session.add(user)
        self._session.flush()
        self._session.refresh(user)
        return user

    def update_password_hash(self, user: User, password_hash: str) -> User:
        """Replace user password hash."""
        user.password_hash = password_hash
        self._session.add(user)
        self._session.flush()
        self._session.refresh(user)
        return user

    def create_google_user(
        self,
        *,
        email: str,
        google_sub: str,
        password_hash: str,
        full_name: str | None,
        avatar_url: str | None,
    ) -> User:
        """Persist a new Google OAuth user account."""
        user = User(
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            avatar_url=avatar_url,
            status=UserStatus.ACTIVE,
            global_role=GlobalRole.USER,
            auth_provider=AuthProvider.GOOGLE.value,
            google_sub=google_sub,
            email_verified_at=datetime.now(UTC),
        )
        self._session.add(user)
        self._session.flush()
        self._session.refresh(user)
        return user

    def link_google_account(
        self,
        user: User,
        *,
        google_sub: str,
        full_name: str | None,
        avatar_url: str | None,
    ) -> User:
        """Link an existing user account to Google."""
        if user.google_sub is None:
            user.google_sub = google_sub
        if user.auth_provider == AuthProvider.LOCAL.value:
            user.auth_provider = AuthProvider.GOOGLE.value
        if user.email_verified_at is None:
            user.email_verified_at = datetime.now(UTC)
            if user.status == UserStatus.PENDING_VERIFICATION:
                user.status = UserStatus.ACTIVE
        if full_name and not user.full_name:
            user.full_name = full_name
        if avatar_url and not user.avatar_url:
            user.avatar_url = avatar_url
        self._session.add(user)
        self._session.flush()
        self._session.refresh(user)
        return user
