"""Auth API integration tests."""

from uuid import uuid4

from app.modules.auth.constants import UserStatus
from app.modules.auth.models import User
from app.modules.auth.password import hash_password
from argon2 import PasswordHasher
from sqlalchemy import select


def test_register_creates_user(auth_client, db_session) -> None:
    email = f"register-{uuid4()}@example.com"
    response = auth_client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "SecurePass123!",
            "full_name": "Register Test",
        },
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["user"]["email"] == email
    assert payload["user"]["status"] == UserStatus.PENDING_VERIFICATION
    assert payload["user"]["global_role"] == "user"
    assert "password" not in response.text
    assert "password_hash" not in response.text


def test_register_duplicate_email_returns_409(auth_client, db_session) -> None:
    email = f"dup-{uuid4()}@example.com"
    first = auth_client.post(
        "/api/auth/register",
        json={"email": email, "password": "SecurePass123!"},
    )
    assert first.status_code == 201

    second = auth_client.post(
        "/api/auth/register",
        json={"email": email, "password": "SecurePass123!"},
    )
    assert second.status_code == 409
    assert second.json()["code"] == "email_already_registered"


def test_login_success_updates_last_login(auth_client, db_session) -> None:
    email = f"login-{uuid4()}@example.com"
    password = "SecurePass123!"
    user = User(
        email=email,
        password_hash=hash_password(password),
        full_name="Login Test",
        status=UserStatus.PENDING_VERIFICATION,
    )
    db_session.add(user)
    db_session.flush()

    response = auth_client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["user"]["email"] == email
    assert payload["user"]["last_login_at"] is not None
    assert payload["tokens"] is None
    assert "jwt" not in response.text.lower()
    assert "refresh" not in response.text.lower()


def test_login_invalid_password_returns_generic_401(auth_client, db_session) -> None:
    email = f"badpass-{uuid4()}@example.com"
    user = User(
        email=email,
        password_hash=hash_password("SecurePass123!"),
        status=UserStatus.PENDING_VERIFICATION,
    )
    db_session.add(user)
    db_session.flush()

    response = auth_client.post(
        "/api/auth/login",
        json={"email": email, "password": "WrongPassword!"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_login_suspended_account_returns_403(auth_client, db_session) -> None:
    email = f"suspended-{uuid4()}@example.com"
    password = "SecurePass123!"
    user = User(
        email=email,
        password_hash=hash_password(password),
        status=UserStatus.SUSPENDED,
    )
    db_session.add(user)
    db_session.flush()

    response = auth_client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 403
    assert response.json()["code"] == "account_inactive"


def test_stored_password_hash_is_argon2id(auth_client, db_session) -> None:
    email = f"argon-{uuid4()}@example.com"
    response = auth_client.post(
        "/api/auth/register",
        json={"email": email, "password": "SecurePass123!"},
    )
    assert response.status_code == 201

    stored = db_session.scalar(select(User).where(User.email == email))
    assert stored is not None
    assert stored.password_hash.startswith("$argon2id$")
    PasswordHasher().verify(stored.password_hash, "SecurePass123!")
