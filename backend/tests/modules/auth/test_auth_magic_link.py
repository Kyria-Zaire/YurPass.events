"""Magic link login tests — TICKET-006D."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from app.main import app
from app.modules.auth.constants import AuthTokenType, UserStatus
from app.modules.auth.dev_outbox import clear_dev_outbox, get_dev_outbox
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
        email=email or f"magic-{uuid4()}@example.com",
        password_hash=hash_password("SecurePass123!"),
        full_name="Magic Test",
        status=status,
    )
    db_session.add(user)
    db_session.flush()
    return user


def _request_magic_link(auth_client, email: str):
    return auth_client.post(
        "/api/auth/request-magic-link",
        json={"email": email},
    )


def test_request_magic_link_success_for_known_email(auth_client, db_session) -> None:
    user = _create_user(db_session)
    response = _request_magic_link(auth_client, user.email)
    assert response.status_code == 200
    assert response.json()["message"] == "magic_link_requested"


def test_request_magic_link_same_success_for_unknown_email(auth_client) -> None:
    response = _request_magic_link(auth_client, "unknown@example.com")
    assert response.status_code == 200
    assert response.json()["message"] == "magic_link_requested"


def test_request_magic_link_no_token_for_unknown_email(auth_client, db_session) -> None:
    email = f"missing-{uuid4()}@example.com"
    before = db_session.scalar(
        select(func.count())
        .select_from(AuthToken)
        .where(AuthToken.token_type == AuthTokenType.MAGIC_LINK.value)
    )
    _request_magic_link(auth_client, email)
    after = db_session.scalar(
        select(func.count())
        .select_from(AuthToken)
        .where(AuthToken.token_type == AuthTokenType.MAGIC_LINK.value)
    )
    assert after == before
    assert get_dev_outbox() == []


def test_request_magic_link_creates_hashed_magic_link_token(auth_client, db_session) -> None:
    user = _create_user(db_session)
    _request_magic_link(auth_client, user.email)

    stored = db_session.scalars(
        select(AuthToken).where(
            AuthToken.user_id == user.id,
            AuthToken.token_type == AuthTokenType.MAGIC_LINK.value,
        )
    ).all()
    assert len(stored) == 1
    assert len(stored[0].token_hash) == 64
    assert stored[0].token_hash != get_dev_outbox()[0]["token"]


def test_request_magic_link_plain_token_absent_from_http_response(
    auth_client,
    db_session,
) -> None:
    user = _create_user(db_session)
    response = _request_magic_link(auth_client, user.email)
    body = response.json()
    assert "token" not in body
    plain = get_dev_outbox()[0]["token"]
    assert plain not in str(body)


def test_verify_magic_link_success_returns_access_token(auth_client, db_session) -> None:
    user = _create_user(db_session)
    _request_magic_link(auth_client, user.email)
    plain = get_dev_outbox()[0]["token"]

    response = auth_client.post("/api/auth/verify-magic-link", json={"token": plain})
    assert response.status_code == 200
    tokens = response.json()["tokens"]
    assert tokens["access_token"]
    assert tokens["token_type"] == "bearer"
    assert tokens["expires_in"] == 900


def test_verify_magic_link_sets_httponly_refresh_cookie(auth_client, db_session) -> None:
    user = _create_user(db_session)
    _request_magic_link(auth_client, user.email)
    plain = get_dev_outbox()[0]["token"]

    response = auth_client.post("/api/auth/verify-magic-link", json={"token": plain})
    set_cookie = response.headers.get("set-cookie", "").lower()
    assert "yurpass_refresh_token=" in set_cookie
    assert "httponly" in set_cookie
    assert auth_client.cookies.get("yurpass_refresh_token")


def test_verify_magic_link_updates_last_login_at(auth_client, db_session) -> None:
    user = _create_user(db_session)
    assert user.last_login_at is None
    _request_magic_link(auth_client, user.email)
    plain = get_dev_outbox()[0]["token"]

    auth_client.post("/api/auth/verify-magic-link", json={"token": plain})

    db_session.refresh(user)
    assert user.last_login_at is not None


def test_verify_magic_link_consumes_token(auth_client, db_session) -> None:
    user = _create_user(db_session)
    _request_magic_link(auth_client, user.email)
    plain = get_dev_outbox()[0]["token"]

    auth_client.post("/api/auth/verify-magic-link", json={"token": plain})

    record = db_session.scalar(
        select(AuthToken).where(AuthToken.token_hash == hash_opaque_token(plain))
    )
    assert record is not None
    assert record.consumed_at is not None


def test_verify_magic_link_refuses_reused_token(auth_client, db_session) -> None:
    user = _create_user(db_session)
    _request_magic_link(auth_client, user.email)
    plain = get_dev_outbox()[0]["token"]

    first = auth_client.post("/api/auth/verify-magic-link", json={"token": plain})
    assert first.status_code == 200

    second = auth_client.post("/api/auth/verify-magic-link", json={"token": plain})
    assert second.status_code == 400
    assert second.json()["code"] == "invalid_auth_token"


def test_verify_magic_link_refuses_expired_token(auth_client, db_session) -> None:
    user = _create_user(db_session)
    _request_magic_link(auth_client, user.email)
    plain = get_dev_outbox()[0]["token"]

    record = db_session.scalar(
        select(AuthToken).where(AuthToken.token_hash == hash_opaque_token(plain))
    )
    record.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    db_session.add(record)
    db_session.flush()

    response = auth_client.post("/api/auth/verify-magic-link", json={"token": plain})
    assert response.status_code == 400
    assert response.json()["code"] == "invalid_auth_token"


def test_verify_magic_link_refuses_invalid_token(auth_client) -> None:
    response = auth_client.post(
        "/api/auth/verify-magic-link",
        json={"token": "not-a-valid-token"},
    )
    assert response.status_code == 400
    assert response.json()["code"] == "invalid_auth_token"


@pytest.mark.parametrize("status", [UserStatus.SUSPENDED, UserStatus.DELETED])
def test_verify_magic_link_refuses_inactive_user(
    auth_client,
    db_session,
    status: UserStatus,
) -> None:
    user = _create_user(db_session, status=status)
    _request_magic_link(auth_client, user.email)
    assert get_dev_outbox() == []

    from app.modules.auth.auth_token_repository import AuthTokenRepository
    from app.modules.auth.tokens import generate_opaque_token

    repo = AuthTokenRepository(db_session)
    plain = generate_opaque_token()
    repo.create(user_id=user.id, plain_token=plain, token_type=AuthTokenType.MAGIC_LINK)

    response = auth_client.post("/api/auth/verify-magic-link", json={"token": plain})
    assert response.status_code == 403
    assert response.json()["code"] == "account_inactive"


def test_password_hash_never_exposed_in_magic_link_flow(auth_client, db_session) -> None:
    user = _create_user(db_session)
    _request_magic_link(auth_client, user.email)
    plain = get_dev_outbox()[0]["token"]

    response = auth_client.post("/api/auth/verify-magic-link", json={"token": plain})
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
        "/google",
        "/google/callback",
    }
    actual = {route.path for route in auth_router.routes if hasattr(route, "methods")}
    assert actual == expected
    assert len([r for r in app.routes if getattr(r, "path", "").startswith("/api/auth")]) == len(
        expected
    )
