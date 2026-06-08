"""Google OAuth tests — TICKET-006F."""

from datetime import UTC, datetime
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

import pytest
from app.core.config import Settings
from app.main import app
from app.modules.auth.constants import AuthProvider, UserStatus
from app.modules.auth.exceptions import OAuthGoogleError
from app.modules.auth.models import AuthToken, RefreshToken, User
from app.modules.auth.oauth_google import GoogleUserInfo, parse_google_userinfo
from app.modules.auth.password import hash_password, verify_password
from app.modules.auth.router import router as auth_router
from sqlalchemy import func, select


@pytest.fixture
def google_auth_client(auth_client, db_session):
    """Auth client with Google OAuth test settings."""
    from app.core.config import get_settings
    from app.db.session import get_db

    settings = Settings(
        app_env="dev",
        jwt_secret="test-jwt-secret",
        google_client_id="test-client-id",
        google_client_secret="test-client-secret",
        google_redirect_uri="http://localhost:8000/api/auth/google/callback",
    )

    def override_get_db():
        try:
            yield db_session
            db_session.flush()
        except Exception:
            raise

    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_db] = override_get_db
    yield auth_client, settings
    app.dependency_overrides.clear()


def _verified_google_user(
    *,
    sub: str | None = None,
    email: str | None = None,
    name: str = "Google User",
) -> GoogleUserInfo:
    return GoogleUserInfo(
        sub=sub or f"google-sub-{uuid4()}",
        email=email or f"google-{uuid4()}@example.com",
        email_verified=True,
        name=name,
        picture="https://lh3.googleusercontent.com/photo.jpg",
    )


def _start_google_oauth(auth_client) -> tuple[str, str]:
    response = auth_client.get("/api/auth/google", follow_redirects=False)
    assert response.status_code == 302
    location = response.headers["location"]
    assert "accounts.google.com" in location
    state = parse_qs(urlparse(location).query)["state"][0]
    cookie_state = auth_client.cookies.get("yurpass_oauth_state")
    assert cookie_state == state
    return state, cookie_state


def _callback(auth_client, *, code: str, state: str):
    return auth_client.get(
        "/api/auth/google/callback",
        params={"code": code, "state": state},
    )


@patch("app.modules.auth.oauth_google.GoogleOAuthClient.authenticate_with_code")
def test_google_start_sets_state_cookie_and_redirects(
    _mock_auth,
    google_auth_client,
) -> None:
    auth_client, settings = google_auth_client
    response = auth_client.get("/api/auth/google", follow_redirects=False)
    assert response.status_code == 302
    location = response.headers["location"]
    assert settings.google_auth_url in location
    assert "client_id=test-client-id" in location
    assert "scope=openid+email+profile" in location.replace("%20", "+")
    set_cookie = response.headers.get("set-cookie", "").lower()
    assert "yurpass_oauth_state=" in set_cookie
    assert "httponly" in set_cookie


@patch("app.modules.auth.oauth_google.GoogleOAuthClient.authenticate_with_code")
def test_callback_refuses_missing_state_cookie(
    _mock_auth,
    google_auth_client,
) -> None:
    auth_client, _settings = google_auth_client
    response = _callback(auth_client, code="auth-code", state="missing-state")
    assert response.status_code == 400
    assert response.json()["code"] == "invalid_oauth_state"


@patch("app.modules.auth.oauth_google.GoogleOAuthClient.authenticate_with_code")
def test_callback_refuses_invalid_state(_mock_auth, google_auth_client) -> None:
    auth_client, _settings = google_auth_client
    state, _cookie_state = _start_google_oauth(auth_client)
    response = _callback(auth_client, code="auth-code", state=f"wrong-{state}")
    assert response.status_code == 400
    assert response.json()["code"] == "invalid_oauth_state"


@patch("app.modules.auth.oauth_google.GoogleOAuthClient.authenticate_with_code")
def test_callback_refuses_unverified_email(mock_auth, google_auth_client) -> None:
    auth_client, _settings = google_auth_client
    mock_auth.side_effect = OAuthGoogleError("Google email not verified")
    state, _ = _start_google_oauth(auth_client)
    response = _callback(auth_client, code="auth-code", state=state)
    assert response.status_code == 400
    assert response.json()["code"] == "oauth_google_error"


def test_parse_google_userinfo_refuses_missing_email() -> None:
    with pytest.raises(OAuthGoogleError) as exc_info:
        parse_google_userinfo({"sub": "abc", "email_verified": True})
    assert exc_info.value.code == "oauth_google_error"


@patch("app.modules.auth.oauth_google.GoogleOAuthClient.authenticate_with_code")
def test_callback_creates_user_for_verified_unknown_email(
    mock_auth,
    google_auth_client,
    db_session,
) -> None:
    auth_client, _settings = google_auth_client
    google_user = _verified_google_user(email="new-google@example.com", sub="sub-new-1")
    mock_auth.return_value = google_user
    state, _ = _start_google_oauth(auth_client)

    response = _callback(auth_client, code="auth-code", state=state)
    assert response.status_code == 200

    user = db_session.scalar(select(User).where(User.email == google_user.email))
    assert user is not None
    assert user.status == UserStatus.ACTIVE
    assert user.email_verified_at is not None
    assert user.auth_provider == AuthProvider.GOOGLE.value
    assert user.google_sub == google_user.sub


@patch("app.modules.auth.oauth_google.GoogleOAuthClient.authenticate_with_code")
def test_callback_links_existing_user_by_email(
    mock_auth,
    google_auth_client,
    db_session,
) -> None:
    auth_client, _settings = google_auth_client
    email = f"existing-{uuid4()}@example.com"
    existing = User(
        email=email,
        password_hash=hash_password("SecurePass123!"),
        full_name="Local User",
        status=UserStatus.PENDING_VERIFICATION,
        auth_provider=AuthProvider.LOCAL.value,
    )
    db_session.add(existing)
    db_session.flush()

    google_user = _verified_google_user(email=email, sub="sub-link-1")
    mock_auth.return_value = google_user
    state, _ = _start_google_oauth(auth_client)

    response = _callback(auth_client, code="auth-code", state=state)
    assert response.status_code == 200

    db_session.refresh(existing)
    assert existing.google_sub == google_user.sub
    assert existing.auth_provider == AuthProvider.GOOGLE.value
    assert existing.email_verified_at is not None
    assert existing.status == UserStatus.ACTIVE
    assert db_session.scalar(select(func.count()).select_from(User).where(User.email == email)) == 1


@patch("app.modules.auth.oauth_google.GoogleOAuthClient.authenticate_with_code")
def test_callback_reuses_existing_user_by_google_sub(
    mock_auth,
    google_auth_client,
    db_session,
) -> None:
    auth_client, _settings = google_auth_client
    google_user = _verified_google_user(sub="sub-reuse-1", email="reuse@example.com")
    existing = User(
        email=google_user.email,
        password_hash=hash_password("SecurePass123!"),
        full_name="Reuse User",
        status=UserStatus.ACTIVE,
        auth_provider=AuthProvider.GOOGLE.value,
        google_sub=google_user.sub,
        email_verified_at=datetime.now(UTC),
    )
    db_session.add(existing)
    db_session.flush()
    user_id = existing.id

    mock_auth.return_value = google_user
    state, _ = _start_google_oauth(auth_client)
    response = _callback(auth_client, code="auth-code", state=state)

    assert response.status_code == 200
    assert response.json()["user"]["id"] == str(user_id)


@patch("app.modules.auth.oauth_google.GoogleOAuthClient.authenticate_with_code")
def test_callback_returns_jwt_and_refresh_cookie(mock_auth, google_auth_client) -> None:
    auth_client, _settings = google_auth_client
    mock_auth.return_value = _verified_google_user()
    state, _ = _start_google_oauth(auth_client)

    response = _callback(auth_client, code="auth-code", state=state)
    assert response.status_code == 200
    assert response.json()["tokens"]["access_token"]
    set_cookie = response.headers.get("set-cookie", "").lower()
    assert "yurpass_refresh_token=" in set_cookie
    assert "httponly" in set_cookie


@patch("app.modules.auth.oauth_google.GoogleOAuthClient.authenticate_with_code")
def test_callback_updates_last_login_at(
    mock_auth,
    google_auth_client,
    db_session,
) -> None:
    auth_client, _settings = google_auth_client
    google_user = _verified_google_user(email="login-time@example.com")
    mock_auth.return_value = google_user
    state, _ = _start_google_oauth(auth_client)

    _callback(auth_client, code="auth-code", state=state)

    user = db_session.scalar(select(User).where(User.email == google_user.email))
    assert user is not None
    assert user.last_login_at is not None


@patch("app.modules.auth.oauth_google.GoogleOAuthClient.authenticate_with_code")
def test_google_user_password_hash_is_non_empty_and_unusable(
    mock_auth,
    google_auth_client,
    db_session,
) -> None:
    auth_client, _settings = google_auth_client
    google_user = _verified_google_user(email="pwd-check@example.com")
    mock_auth.return_value = google_user
    state, _ = _start_google_oauth(auth_client)
    _callback(auth_client, code="auth-code", state=state)

    user = db_session.scalar(select(User).where(User.email == google_user.email))
    assert user is not None
    assert user.password_hash
    assert not verify_password("SecurePass123!", user.password_hash)


@patch("app.modules.auth.oauth_google.GoogleOAuthClient.authenticate_with_code")
def test_google_tokens_are_not_persisted(mock_auth, google_auth_client) -> None:
    auth_client, _settings = google_auth_client
    mock_auth.return_value = _verified_google_user()
    state, _ = _start_google_oauth(auth_client)
    _callback(auth_client, code="auth-code", state=state)

    for model in (User, RefreshToken, AuthToken):
        column_names = {column.name for column in model.__table__.columns}
        assert "google_access_token" not in column_names
        assert "google_refresh_token" not in column_names


@patch("app.modules.auth.oauth_google.GoogleOAuthClient.authenticate_with_code")
def test_callback_clears_oauth_state_cookie_on_success(mock_auth, google_auth_client) -> None:
    auth_client, _settings = google_auth_client
    mock_auth.return_value = _verified_google_user()
    state, _ = _start_google_oauth(auth_client)
    response = _callback(auth_client, code="auth-code", state=state)
    set_cookie = response.headers.get("set-cookie", "").lower()
    assert "yurpass_oauth_state=" in set_cookie


@patch("app.modules.auth.oauth_google.GoogleOAuthClient.authenticate_with_code")
def test_callback_password_hash_not_exposed(mock_auth, google_auth_client) -> None:
    auth_client, _settings = google_auth_client
    mock_auth.return_value = _verified_google_user()
    state, _ = _start_google_oauth(auth_client)
    response = _callback(auth_client, code="auth-code", state=state)
    payload = response.json()
    assert "password_hash" not in payload
    assert "password_hash" not in payload["user"]


@patch("app.modules.auth.oauth_google.GoogleOAuthClient.authenticate_with_code")
def test_callback_refuses_suspended_user(
    mock_auth,
    google_auth_client,
    db_session,
) -> None:
    auth_client, _settings = google_auth_client
    email = f"suspended-{uuid4()}@example.com"
    user = User(
        email=email,
        password_hash=hash_password("SecurePass123!"),
        status=UserStatus.SUSPENDED,
        auth_provider=AuthProvider.LOCAL.value,
    )
    db_session.add(user)
    db_session.flush()

    mock_auth.return_value = _verified_google_user(email=email, sub="sub-suspended")
    state, _ = _start_google_oauth(auth_client)
    response = _callback(auth_client, code="auth-code", state=state)
    assert response.status_code == 403
    assert response.json()["code"] == "account_inactive"


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
