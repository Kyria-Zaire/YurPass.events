"""OTP email login tests — TICKET-006E."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from app.core.config import Settings, get_settings
from app.main import app
from app.modules.auth.constants import AuthTokenType, UserStatus
from app.modules.auth.dev_outbox import clear_dev_outbox, get_dev_outbox, record_dev_auth_link
from app.modules.auth.models import AuthToken, User
from app.modules.auth.password import hash_password
from app.modules.auth.router import router as auth_router
from app.modules.auth.tokens import hash_opaque_token
from sqlalchemy import func, select


@pytest.fixture(autouse=True)
def _clear_dev_outbox() -> None:
    clear_dev_outbox()
    yield
    clear_dev_outbox()


def _create_user(
    db_session,
    email: str | None = None,
    *,
    status: UserStatus = UserStatus.ACTIVE,
) -> User:
    user = User(
        email=email or f"otp-{uuid4()}@example.com",
        password_hash=hash_password("SecurePass123!"),
        full_name="OTP Test",
        status=status,
    )
    db_session.add(user)
    db_session.flush()
    return user


def _request_otp(auth_client, email: str):
    return auth_client.post("/api/auth/request-otp", json={"email": email})


def test_request_otp_success_for_known_email(auth_client, db_session) -> None:
    user = _create_user(db_session)
    response = _request_otp(auth_client, user.email)
    assert response.status_code == 200
    assert response.json()["message"] == "otp_requested"


def test_request_otp_same_success_for_unknown_email(auth_client) -> None:
    response = _request_otp(auth_client, f"unknown-{uuid4()}@example.com")
    assert response.status_code == 200
    assert response.json()["message"] == "otp_requested"


def test_request_otp_no_token_for_unknown_email(auth_client, db_session) -> None:
    email = f"missing-{uuid4()}@example.com"
    before = db_session.scalar(
        select(func.count())
        .select_from(AuthToken)
        .where(AuthToken.token_type == AuthTokenType.OTP_LOGIN.value)
    )
    _request_otp(auth_client, email)
    after = db_session.scalar(
        select(func.count())
        .select_from(AuthToken)
        .where(AuthToken.token_type == AuthTokenType.OTP_LOGIN.value)
    )
    assert after == before
    assert get_dev_outbox() == []


@pytest.mark.parametrize("status", [UserStatus.SUSPENDED, UserStatus.DELETED])
def test_request_otp_no_token_for_inactive_user(
    auth_client,
    db_session,
    status: UserStatus,
) -> None:
    user = _create_user(db_session, status=status)
    before = db_session.scalar(
        select(func.count())
        .select_from(AuthToken)
        .where(AuthToken.token_type == AuthTokenType.OTP_LOGIN.value)
    )
    _request_otp(auth_client, user.email)
    after = db_session.scalar(
        select(func.count())
        .select_from(AuthToken)
        .where(AuthToken.token_type == AuthTokenType.OTP_LOGIN.value)
    )
    assert after == before
    assert get_dev_outbox() == []


@pytest.mark.parametrize("status", [UserStatus.ACTIVE, UserStatus.PENDING_VERIFICATION])
def test_request_otp_creates_hashed_otp_login_token(
    auth_client,
    db_session,
    status: UserStatus,
) -> None:
    user = _create_user(db_session, status=status)
    _request_otp(auth_client, user.email)

    stored = db_session.scalars(
        select(AuthToken).where(
            AuthToken.user_id == user.id,
            AuthToken.token_type == AuthTokenType.OTP_LOGIN.value,
        )
    ).all()
    assert len(stored) == 1
    assert len(stored[0].token_hash) == 64
    otp_code = get_dev_outbox()[0]["token"]
    assert len(otp_code) == 6
    assert otp_code.isdigit()
    assert stored[0].token_hash != otp_code


def test_request_otp_plain_code_absent_from_http_response(auth_client, db_session) -> None:
    user = _create_user(db_session)
    response = _request_otp(auth_client, user.email)
    body = response.json()
    assert "code" not in body
    assert "token" not in body
    otp_code = get_dev_outbox()[0]["token"]
    assert otp_code not in str(body)


def test_dev_outbox_receives_otp_code_in_dev_local() -> None:
    production_settings = Settings(app_env="production", jwt_secret="test-secret")
    record_dev_auth_link(
        settings=production_settings,
        kind="otp_login",
        email="user@example.com",
        plain_token="123456",
        path="/api/auth/verify-otp",
    )
    assert get_dev_outbox() == []

    local_settings = Settings(app_env="local", jwt_secret="test-secret")
    record_dev_auth_link(
        settings=local_settings,
        kind="otp_login",
        email="user@example.com",
        plain_token="654321",
        path="/api/auth/verify-otp",
    )
    assert get_dev_outbox()[0]["token"] == "654321"

    clear_dev_outbox()
    dev_settings = get_settings()
    record_dev_auth_link(
        settings=dev_settings,
        kind="otp_login",
        email="user@example.com",
        plain_token="111222",
        path="/api/auth/verify-otp",
    )
    assert get_dev_outbox()[0]["token"] == "111222"


def test_verify_otp_success_returns_access_token(auth_client, db_session) -> None:
    user = _create_user(db_session)
    _request_otp(auth_client, user.email)
    otp_code = get_dev_outbox()[0]["token"]

    response = auth_client.post(
        "/api/auth/verify-otp",
        json={"email": user.email, "code": otp_code},
    )
    assert response.status_code == 200
    tokens = response.json()["tokens"]
    assert tokens["access_token"]
    assert tokens["token_type"] == "bearer"
    assert tokens["expires_in"] == 900


def test_verify_otp_sets_httponly_refresh_cookie(auth_client, db_session) -> None:
    user = _create_user(db_session)
    _request_otp(auth_client, user.email)
    otp_code = get_dev_outbox()[0]["token"]

    response = auth_client.post(
        "/api/auth/verify-otp",
        json={"email": user.email, "code": otp_code},
    )
    set_cookie = response.headers.get("set-cookie", "").lower()
    assert "yurpass_refresh_token=" in set_cookie
    assert "httponly" in set_cookie
    assert auth_client.cookies.get("yurpass_refresh_token")


def test_verify_otp_updates_last_login_at(auth_client, db_session) -> None:
    user = _create_user(db_session)
    assert user.last_login_at is None
    _request_otp(auth_client, user.email)
    otp_code = get_dev_outbox()[0]["token"]

    auth_client.post("/api/auth/verify-otp", json={"email": user.email, "code": otp_code})

    db_session.refresh(user)
    assert user.last_login_at is not None


def test_verify_otp_consumes_token(auth_client, db_session) -> None:
    user = _create_user(db_session)
    _request_otp(auth_client, user.email)
    otp_code = get_dev_outbox()[0]["token"]

    auth_client.post("/api/auth/verify-otp", json={"email": user.email, "code": otp_code})

    record = db_session.scalar(
        select(AuthToken).where(AuthToken.token_hash == hash_opaque_token(otp_code))
    )
    assert record is not None
    assert record.consumed_at is not None


def test_verify_otp_refuses_reused_code(auth_client, db_session) -> None:
    user = _create_user(db_session)
    _request_otp(auth_client, user.email)
    otp_code = get_dev_outbox()[0]["token"]
    payload = {"email": user.email, "code": otp_code}

    first = auth_client.post("/api/auth/verify-otp", json=payload)
    assert first.status_code == 200

    second = auth_client.post("/api/auth/verify-otp", json=payload)
    assert second.status_code == 401
    assert second.json()["detail"] == "invalid_otp"


def test_verify_otp_refuses_expired_code(auth_client, db_session) -> None:
    user = _create_user(db_session)
    _request_otp(auth_client, user.email)
    otp_code = get_dev_outbox()[0]["token"]

    record = db_session.scalar(
        select(AuthToken).where(AuthToken.token_hash == hash_opaque_token(otp_code))
    )
    record.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    db_session.add(record)
    db_session.flush()

    response = auth_client.post(
        "/api/auth/verify-otp",
        json={"email": user.email, "code": otp_code},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_otp"


def test_verify_otp_refuses_invalid_code(auth_client, db_session) -> None:
    user = _create_user(db_session)
    _request_otp(auth_client, user.email)

    response = auth_client.post(
        "/api/auth/verify-otp",
        json={"email": user.email, "code": "000000"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_otp"


def test_verify_otp_refuses_non_six_digit_format(auth_client, db_session) -> None:
    user = _create_user(db_session)
    response = auth_client.post(
        "/api/auth/verify-otp",
        json={"email": user.email, "code": "12345"},
    )
    assert response.status_code == 422


@pytest.mark.parametrize("status", [UserStatus.SUSPENDED, UserStatus.DELETED])
def test_verify_otp_refuses_inactive_user(
    auth_client,
    db_session,
    status: UserStatus,
) -> None:
    user = _create_user(db_session, status=status)
    from app.modules.auth.auth_token_repository import AuthTokenRepository
    from app.modules.auth.tokens import generate_otp_code

    repo = AuthTokenRepository(db_session)
    otp_code = generate_otp_code()
    repo.create(user_id=user.id, plain_token=otp_code, token_type=AuthTokenType.OTP_LOGIN)

    response = auth_client.post(
        "/api/auth/verify-otp",
        json={"email": user.email, "code": otp_code},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_otp"


def test_password_hash_never_exposed_in_otp_flow(auth_client, db_session) -> None:
    user = _create_user(db_session)
    _request_otp(auth_client, user.email)
    otp_code = get_dev_outbox()[0]["token"]

    response = auth_client.post(
        "/api/auth/verify-otp",
        json={"email": user.email, "code": otp_code},
    )
    payload = response.json()
    assert "password_hash" not in payload
    assert "password_hash" not in payload["user"]
    assert user.password_hash not in str(payload)


def test_no_extra_auth_endpoints_beyond_scope() -> None:
    expected = {
        "/register",
        "/login",
        "/refresh",
        "/logout",
        "/me",
        "/request-email-verification",
        "/verify-email",
        "/request-password-reset",
        "/reset-password",
        "/request-magic-link",
        "/verify-magic-link",
        "/request-otp",
        "/verify-otp",
    }
    actual = {route.path for route in auth_router.routes if hasattr(route, "methods")}
    assert actual == expected
    assert len([r for r in app.routes if getattr(r, "path", "").startswith("/api/auth")]) == len(
        expected
    )
