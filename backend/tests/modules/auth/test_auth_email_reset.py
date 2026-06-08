"""Email verification and password reset tests — TICKET-006C."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from app.core.config import Settings, get_settings
from app.modules.auth.constants import AuthTokenType, UserStatus
from app.modules.auth.dev_outbox import clear_dev_outbox, get_dev_outbox, record_dev_auth_link
from app.modules.auth.models import AuthToken, RefreshToken, User
from app.modules.auth.password import hash_password, verify_password
from app.modules.auth.tokens import generate_opaque_token, hash_opaque_token
from sqlalchemy import select


@pytest.fixture(autouse=True)
def _clear_dev_outbox() -> None:
    clear_dev_outbox()
    yield
    clear_dev_outbox()


def _create_user(
    db_session,
    email: str | None = None,
    password: str = "SecurePass123!",
) -> tuple[User, str]:
    email = email or f"erc-{uuid4()}@example.com"
    user = User(
        email=email,
        password_hash=hash_password(password),
        full_name="ERC Test",
        status=UserStatus.PENDING_VERIFICATION,
    )
    db_session.add(user)
    db_session.flush()
    return user, password


def _access_token(auth_client, email: str, password: str) -> str:
    response = auth_client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    return response.json()["tokens"]["access_token"]


def test_request_email_verification_requires_auth(auth_client) -> None:
    response = auth_client.post("/api/auth/request-email-verification")
    assert response.status_code == 401


def test_request_email_verification_creates_hashed_token(auth_client, db_session) -> None:
    user, password = _create_user(db_session)
    token = _access_token(auth_client, user.email, password)

    response = auth_client.post(
        "/api/auth/request-email-verification",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "verification_email_requested"

    stored = db_session.scalars(
        select(AuthToken).where(
            AuthToken.user_id == user.id,
            AuthToken.token_type == AuthTokenType.EMAIL_VERIFICATION.value,
        )
    ).all()
    assert len(stored) == 1
    assert stored[0].token_hash != get_dev_outbox()[0]["token"]
    assert len(stored[0].token_hash) == 64


def test_verify_email_success_sets_email_verified_at(auth_client, db_session) -> None:
    user, password = _create_user(db_session)
    token = _access_token(auth_client, user.email, password)
    auth_client.post(
        "/api/auth/request-email-verification",
        headers={"Authorization": f"Bearer {token}"},
    )
    plain = get_dev_outbox()[0]["token"]

    response = auth_client.post("/api/auth/verify-email", json={"token": plain})
    assert response.status_code == 200
    assert response.json()["message"] == "email_verified"

    db_session.refresh(user)
    assert user.email_verified_at is not None
    assert user.status == UserStatus.ACTIVE


def test_verify_email_invalid_returns_400(auth_client) -> None:
    response = auth_client.post("/api/auth/verify-email", json={"token": "invalid-token"})
    assert response.status_code == 400
    assert response.json()["code"] == "invalid_auth_token"


def test_verify_email_consumed_token_refused(auth_client, db_session) -> None:
    user, password = _create_user(db_session)
    access = _access_token(auth_client, user.email, password)
    auth_client.post(
        "/api/auth/request-email-verification",
        headers={"Authorization": f"Bearer {access}"},
    )
    plain = get_dev_outbox()[0]["token"]

    first = auth_client.post("/api/auth/verify-email", json={"token": plain})
    assert first.status_code == 200

    second = auth_client.post("/api/auth/verify-email", json={"token": plain})
    assert second.status_code == 400


def test_request_password_reset_unknown_email_stable(auth_client) -> None:
    response = auth_client.post(
        "/api/auth/request-password-reset",
        json={"email": f"unknown-{uuid4()}@example.com"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "password_reset_requested"
    assert get_dev_outbox() == []


def test_request_password_reset_creates_token_if_known(auth_client, db_session) -> None:
    user, _ = _create_user(db_session)
    response = auth_client.post(
        "/api/auth/request-password-reset",
        json={"email": user.email},
    )
    assert response.status_code == 200

    stored = db_session.scalar(
        select(AuthToken).where(
            AuthToken.user_id == user.id,
            AuthToken.token_type == AuthTokenType.PASSWORD_RESET.value,
        )
    )
    assert stored is not None
    assert get_dev_outbox()[0]["kind"] == "password_reset"


def test_reset_password_changes_hash(auth_client, db_session) -> None:
    user, password = _create_user(db_session)
    auth_client.post("/api/auth/request-password-reset", json={"email": user.email})
    plain = get_dev_outbox()[0]["token"]
    old_hash = user.password_hash

    response = auth_client.post(
        "/api/auth/reset-password",
        json={"token": plain, "new_password": "NewSecure456!"},
    )
    assert response.status_code == 200

    db_session.refresh(user)
    assert user.password_hash != old_hash
    assert verify_password("NewSecure456!", user.password_hash)


def test_reset_password_allows_login_with_new_password(auth_client, db_session) -> None:
    user, password = _create_user(db_session)
    auth_client.post("/api/auth/request-password-reset", json={"email": user.email})
    plain = get_dev_outbox()[0]["token"]
    auth_client.post(
        "/api/auth/reset-password",
        json={"token": plain, "new_password": "NewSecure456!"},
    )

    old_login = auth_client.post(
        "/api/auth/login",
        json={"email": user.email, "password": password},
    )
    assert old_login.status_code == 401

    new_login = auth_client.post(
        "/api/auth/login",
        json={"email": user.email, "password": "NewSecure456!"},
    )
    assert new_login.status_code == 200


def test_reset_password_revokes_active_refresh_tokens(auth_client, db_session) -> None:
    user, password = _create_user(db_session)
    _access_token(auth_client, user.email, password)

    refresh_records = list(
        db_session.scalars(select(RefreshToken).where(RefreshToken.user_id == user.id))
    )
    assert refresh_records
    assert all(record.revoked_at is None for record in refresh_records)

    auth_client.post("/api/auth/request-password-reset", json={"email": user.email})
    plain = get_dev_outbox()[-1]["token"]
    auth_client.post(
        "/api/auth/reset-password",
        json={"token": plain, "new_password": "NewSecure456!"},
    )

    for record in refresh_records:
        db_session.refresh(record)
        assert record.revoked_at is not None


def test_reset_password_expired_token_refused(auth_client, db_session) -> None:
    user, _ = _create_user(db_session)
    plain = generate_opaque_token()
    expired = AuthToken(
        user_id=user.id,
        token_hash=hash_opaque_token(plain),
        token_type=AuthTokenType.PASSWORD_RESET.value,
        expires_at=datetime.now(UTC) - timedelta(minutes=1),
    )
    db_session.add(expired)
    db_session.flush()

    response = auth_client.post(
        "/api/auth/reset-password",
        json={"token": plain, "new_password": "NewSecure456!"},
    )
    assert response.status_code == 400


def test_reset_password_consumed_token_refused(auth_client, db_session) -> None:
    user, _ = _create_user(db_session)
    auth_client.post("/api/auth/request-password-reset", json={"email": user.email})
    plain = get_dev_outbox()[0]["token"]

    first = auth_client.post(
        "/api/auth/reset-password",
        json={"token": plain, "new_password": "NewSecure456!"},
    )
    assert first.status_code == 200

    second = auth_client.post(
        "/api/auth/reset-password",
        json={"token": plain, "new_password": "AnotherPass789!"},
    )
    assert second.status_code == 400


def test_no_plain_token_stored_in_database(auth_client, db_session) -> None:
    user, password = _create_user(db_session)
    access = _access_token(auth_client, user.email, password)
    auth_client.post(
        "/api/auth/request-email-verification",
        headers={"Authorization": f"Bearer {access}"},
    )
    plain = get_dev_outbox()[0]["token"]

    rows = db_session.scalars(select(AuthToken)).all()
    for row in rows:
        assert row.token_hash != plain
        assert len(row.token_hash) == 64


def test_dev_outbox_active_only_in_dev_and_local() -> None:
    production_settings = Settings(app_env="production", jwt_secret="test-secret")
    record_dev_auth_link(
        settings=production_settings,
        kind="password_reset",
        email="user@example.com",
        plain_token="should-not-store",
        path="/api/auth/reset-password",
    )
    assert get_dev_outbox() == []

    local_settings = Settings(app_env="local", jwt_secret="test-secret")
    record_dev_auth_link(
        settings=local_settings,
        kind="password_reset",
        email="user@example.com",
        plain_token="local-token",
        path="/api/auth/reset-password",
    )
    assert len(get_dev_outbox()) == 1

    clear_dev_outbox()
    dev_settings = get_settings()
    record_dev_auth_link(
        settings=dev_settings,
        kind="password_reset",
        email="user@example.com",
        plain_token="dev-token",
        path="/api/auth/reset-password",
    )
    assert len(get_dev_outbox()) == 1
