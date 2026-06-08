"""Auth session tests — TICKET-006B JWT + refresh tokens."""

from uuid import uuid4

from app.modules.auth.constants import UserStatus
from app.modules.auth.models import RefreshToken, User
from app.modules.auth.password import hash_password
from app.modules.auth.tokens import hash_refresh_token
from sqlalchemy import select


def _create_user(
    db_session,
    email: str | None = None,
    password: str = "SecurePass123!",
) -> tuple[str, str]:
    email = email or f"session-{uuid4()}@example.com"
    user = User(
        email=email,
        password_hash=hash_password(password),
        full_name="Session Test",
        status=UserStatus.PENDING_VERIFICATION,
    )
    db_session.add(user)
    db_session.flush()
    return email, password


def _login(auth_client, email: str, password: str):
    return auth_client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )


def test_login_returns_access_token(auth_client, db_session) -> None:
    email, password = _create_user(db_session)
    response = _login(auth_client, email, password)
    assert response.status_code == 200
    tokens = response.json()["tokens"]
    assert tokens["access_token"]
    assert tokens["token_type"] == "bearer"
    assert tokens["expires_in"] == 900


def test_login_sets_httponly_refresh_cookie(auth_client, db_session) -> None:
    email, password = _create_user(db_session)
    response = _login(auth_client, email, password)
    set_cookie = response.headers.get("set-cookie", "").lower()
    assert "yurpass_refresh_token=" in set_cookie
    assert "httponly" in set_cookie
    assert auth_client.cookies.get("yurpass_refresh_token")


def test_me_works_with_access_token(auth_client, db_session) -> None:
    email, password = _create_user(db_session)
    login = _login(auth_client, email, password)
    access_token = login.json()["tokens"]["access_token"]

    response = auth_client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["email"] == email
    assert payload["global_role"] == "user"
    assert "organization" not in response.text.lower()
    assert "password_hash" not in response.text


def test_me_rejects_missing_token(auth_client) -> None:
    response = auth_client.get("/api/auth/me")
    assert response.status_code == 401


def test_me_rejects_invalid_token(auth_client) -> None:
    response = auth_client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer invalid.token.value"},
    )
    assert response.status_code == 401


def test_refresh_returns_new_access_token(auth_client, db_session) -> None:
    email, password = _create_user(db_session)
    _login(auth_client, email, password)

    response = auth_client.post("/api/auth/refresh")
    assert response.status_code == 200
    assert response.json()["tokens"]["access_token"]


def test_refresh_rotates_token(auth_client, db_session) -> None:
    email, password = _create_user(db_session)
    _login(auth_client, email, password)
    old_refresh = auth_client.cookies.get("yurpass_refresh_token")

    auth_client.post("/api/auth/refresh")

    stored_old = db_session.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(old_refresh))
    )
    assert stored_old is not None
    assert stored_old.rotated_at is not None
    assert stored_old.revoked_at is not None


def test_old_refresh_token_cannot_be_reused(auth_client, db_session) -> None:
    email, password = _create_user(db_session)
    _login(auth_client, email, password)
    old_refresh = auth_client.cookies.get("yurpass_refresh_token")

    auth_client.post("/api/auth/refresh")

    auth_client.cookies.set("yurpass_refresh_token", old_refresh)
    response = auth_client.post("/api/auth/refresh")
    assert response.status_code == 401


def test_logout_revokes_refresh_token(auth_client, db_session) -> None:
    email, password = _create_user(db_session)
    _login(auth_client, email, password)
    plain_refresh = auth_client.cookies.get("yurpass_refresh_token")

    response = auth_client.post("/api/auth/logout")
    assert response.status_code == 200
    assert response.json()["message"] == "logout_success"

    stored = db_session.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(plain_refresh))
    )
    assert stored is not None
    assert stored.revoked_at is not None


def test_logout_clears_cookie(auth_client, db_session) -> None:
    email, password = _create_user(db_session)
    _login(auth_client, email, password)

    response = auth_client.post("/api/auth/logout")
    set_cookie = response.headers.get("set-cookie", "").lower()
    assert "yurpass_refresh_token=" in set_cookie


def test_refresh_without_cookie_returns_401(auth_client) -> None:
    response = auth_client.post("/api/auth/refresh")
    assert response.status_code == 401


def test_password_hash_never_exposed_in_session_flow(auth_client, db_session) -> None:
    email, password = _create_user(db_session)
    login = _login(auth_client, email, password)
    access_token = login.json()["tokens"]["access_token"]

    me = auth_client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    refresh = auth_client.post("/api/auth/refresh")

    for response in (login, me, refresh):
        assert "password_hash" not in response.text
        assert "password" not in response.json()
