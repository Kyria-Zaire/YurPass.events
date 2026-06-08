"""Authentication business logic."""

from app.modules.auth.constants import UserStatus
from app.modules.auth.exceptions import (
    AccountInactiveError,
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
)
from app.modules.auth.models import User
from app.modules.auth.password import hash_password, verify_password
from app.modules.auth.repository import AuthRepository
from app.modules.auth.schemas import LoginResponse, RegisterResponse, UserPublic


def normalize_email(email: str) -> str:
    """Normalize email for storage and lookup."""
    return email.strip().lower()


class AuthService:
    """Service layer for Authentication module."""

    def __init__(self, repository: AuthRepository) -> None:
        self._repository = repository

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

    def login(self, *, email: str, password: str) -> LoginResponse:
        """Authenticate a user with email and password."""
        normalized_email = normalize_email(email)
        user = self._repository.get_by_email(normalized_email)

        if user is None or not verify_password(password, user.password_hash):
            raise InvalidCredentialsError()

        if user.status in {UserStatus.SUSPENDED, UserStatus.DELETED}:
            raise AccountInactiveError(status=user.status.value)

        user = self._repository.update_last_login(user)
        return LoginResponse(user=UserPublic.model_validate(user))

    @staticmethod
    def to_public(user: User) -> UserPublic:
        """Map a User entity to a public schema."""
        return UserPublic.model_validate(user)
