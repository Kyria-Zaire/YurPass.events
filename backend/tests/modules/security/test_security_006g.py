"""Security hardening tests — TICKET-006G."""

import inspect
from uuid import uuid4

import pytest
from app.core.config import Settings, get_settings
from app.core.rate_limit import check_rate_limit, reset_rate_limits
from app.core.turnstile import TurnstileService
from app.modules.audit.constants import AuditAction
from app.modules.audit.models import AuditLog
from app.modules.audit.repository import AuditRepository
from app.modules.audit.service import AuditService
from app.modules.auth.constants import GlobalRole, UserStatus
from app.modules.auth.models import RefreshToken, User
from app.modules.auth.password import hash_password
from app.modules.auth.permissions import require_global_roles, require_super_admin
from app.modules.auth.tokens import create_access_token, hash_refresh_token
from app.shared.exceptions import PermissionDeniedError
from fastapi import Request
from sqlalchemy import select


def _create_user(
    db_session,
    *,
    email: str | None = None,
    password: str = "SecurePass123!",
    global_role: GlobalRole = GlobalRole.USER,
    status: UserStatus = UserStatus.ACTIVE,
) -> User:
    user = User(
        email=email or f"sec-{uuid4()}@example.com",
        password_hash=hash_password(password),
        full_name="Security Test",
        status=status,
        global_role=global_role,
    )
    db_session.add(user)
    db_session.flush()
    return user


def _bearer(user: User, settings: Settings | None = None) -> dict[str, str]:
    active_settings = settings or get_settings()
    token, _ = create_access_token(user, active_settings)
    return {"Authorization": f"Bearer {token}"}


def test_require_global_roles_accepts_global_role_enum() -> None:
    signature = inspect.signature(require_global_roles)
    assert signature.parameters["allowed_roles"].annotation is GlobalRole


def test_require_super_admin_rejects_user(db_session) -> None:
    user = _create_user(db_session, global_role=GlobalRole.USER)
    guard = require_super_admin
    with pytest.raises(PermissionDeniedError):
        guard(user=user)


def test_require_super_admin_rejects_admin(db_session) -> None:
    user = _create_user(db_session, global_role=GlobalRole.ADMIN)
    guard = require_super_admin
    with pytest.raises(PermissionDeniedError):
        guard(user=user)


def test_require_active_user_rejects_suspended(db_session) -> None:
    from app.modules.auth.permissions import require_active_user

    user = _create_user(db_session, status=UserStatus.SUSPENDED)
    with pytest.raises(PermissionDeniedError):
        require_active_user(user=user)


def test_login_success_creates_audit_log(auth_client, db_session) -> None:
    email = f"audit-{uuid4()}@example.com"
    password = "SecurePass123!"
    _create_user(db_session, email=email, password=password)

    response = auth_client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200

    logs = list(db_session.scalars(select(AuditLog).where(AuditLog.action == "login_success")))
    assert len(logs) == 1
    assert logs[0].actor_user_id is not None
    assert "password" not in str(logs[0].audit_metadata or {})


def test_audit_resource_id_accepts_non_uuid_string(db_session) -> None:
    service = AuditService(AuditRepository(db_session))
    record = service.record(
        AuditAction.LOGIN_SUCCESS.value,
        resource_type="payment",
        resource_id="stripe_pi_3NxAbC123",
    )
    assert record.resource_id == "stripe_pi_3NxAbC123"


def test_rate_limit_disabled_by_default_in_tests(auth_client, db_session, monkeypatch) -> None:
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "false")
    get_settings.cache_clear()
    reset_rate_limits()

    email = f"rl-off-{uuid4()}@example.com"
    _create_user(db_session, email=email)
    for _ in range(15):
        response = auth_client.post(
            "/api/auth/login",
            json={"email": email, "password": "wrong-password"},
        )
        assert response.status_code == 401


def test_rate_limit_blocks_when_enabled(monkeypatch) -> None:
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")
    get_settings.cache_clear()
    reset_rate_limits()

    settings = get_settings()
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/auth/login",
        "headers": [(b"host", b"testserver")],
        "client": ("127.0.0.1", 12345),
    }

    async def receive():
        return {"type": "http.request"}

    request = Request(scope, receive)

    for _ in range(10):
        check_rate_limit(request, limit=10, window_seconds=60, settings=settings)

    with pytest.raises(Exception) as exc_info:
        check_rate_limit(request, limit=10, window_seconds=60, settings=settings)
    assert exc_info.value.status_code == 429


def test_security_headers_present(client) -> None:
    response = client.get("/api/health")
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("Referrer-Policy") == "no-referrer"
    assert "camera=()" in response.headers.get("Permissions-Policy", "")


def test_refresh_reuse_revokes_session_tokens(auth_client, db_session) -> None:
    email = f"reuse-{uuid4()}@example.com"
    password = "SecurePass123!"
    _create_user(db_session, email=email, password=password)

    login = auth_client.post("/api/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200
    old_refresh = auth_client.cookies.get("yurpass_refresh_token")

    rotate = auth_client.post("/api/auth/refresh")
    assert rotate.status_code == 200
    new_refresh = auth_client.cookies.get("yurpass_refresh_token")
    assert new_refresh != old_refresh

    auth_client.cookies.set("yurpass_refresh_token", old_refresh)
    reuse = auth_client.post("/api/auth/refresh")
    assert reuse.status_code == 401

    reuse_logs = list(
        db_session.scalars(
            select(AuditLog).where(AuditLog.action == AuditAction.REFRESH_REUSE_DETECTED.value)
        )
    )
    assert len(reuse_logs) == 1

    auth_client.cookies.set("yurpass_refresh_token", new_refresh)
    blocked = auth_client.post("/api/auth/refresh")
    assert blocked.status_code == 401

    session_id = db_session.scalar(
        select(RefreshToken.session_id).where(
            RefreshToken.token_hash == hash_refresh_token(old_refresh)
        )
    )
    active_in_session = list(
        db_session.scalars(
            select(RefreshToken).where(
                RefreshToken.session_id == session_id,
                RefreshToken.revoked_at.is_(None),
            )
        )
    )
    assert active_in_session == []


def test_admin_rbac_diagnostic_via_service_layer(auth_client, db_session) -> None:
    super_admin = _create_user(db_session, global_role=GlobalRole.SUPER_ADMIN)
    headers = _bearer(super_admin)

    response = auth_client.get("/api/admin/rbac/diagnostic", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["global_role"] == "super_admin"
    assert "admin.rbac.diagnostic" in payload["permissions"]


def test_admin_rbac_diagnostic_rejects_non_super_admin(auth_client, db_session) -> None:
    admin_user = _create_user(db_session, global_role=GlobalRole.ADMIN)
    headers = _bearer(admin_user)

    response = auth_client.get("/api/admin/rbac/diagnostic", headers=headers)
    assert response.status_code == 403
    assert response.json()["code"] == "permission_denied"


def test_turnstile_disabled_by_default() -> None:
    service = TurnstileService(get_settings())
    assert service.verify(None) is True
