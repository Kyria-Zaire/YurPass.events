"""Auth service unit tests."""

from datetime import UTC, datetime
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from app.modules.auth.constants import GlobalRole, UserStatus
from app.modules.auth.exceptions import (
    AccountInactiveError,
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
)
from app.modules.auth.models import User
from app.modules.auth.password import hash_password
from app.modules.auth.service import AuthService

_TEST_PASSWORD = "SecurePass123!"


def _make_user(**overrides) -> User:
    user = User(
        id=uuid4(),
        email="user@example.com",
        password_hash=hash_password(_TEST_PASSWORD),
        full_name="Test User",
        status=UserStatus.PENDING_VERIFICATION,
        global_role=GlobalRole.USER,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    for key, value in overrides.items():
        setattr(user, key, value)
    return user


def test_register_raises_when_email_exists() -> None:
    repository = MagicMock()
    repository.get_by_email.return_value = _make_user()
    service = AuthService(repository)

    with pytest.raises(EmailAlreadyRegisteredError):
        service.register(
            email="user@example.com",
            password="SecurePass123!",
            full_name="Test",
        )


def test_login_raises_invalid_credentials_when_user_missing() -> None:
    repository = MagicMock()
    repository.get_by_email.return_value = None
    service = AuthService(repository)

    with pytest.raises(InvalidCredentialsError):
        service.login(email="missing@example.com", password="SecurePass123!")


def test_login_raises_when_account_suspended() -> None:
    repository = MagicMock()
    repository.get_by_email.return_value = _make_user(status=UserStatus.SUSPENDED)
    service = AuthService(repository)

    with pytest.raises(AccountInactiveError):
        service.login(email="user@example.com", password=_TEST_PASSWORD)
