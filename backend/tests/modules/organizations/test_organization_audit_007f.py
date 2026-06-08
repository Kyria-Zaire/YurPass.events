"""Organization audit consolidation tests — TICKET-007F."""

from uuid import uuid4

from app.core.config import get_settings
from app.modules.audit.constants import AuditAction
from app.modules.audit.models import AuditLog
from app.modules.audit.repository import AuditRepository
from app.modules.audit.service import AuditService
from app.modules.auth.constants import GlobalRole, UserStatus
from app.modules.auth.models import User
from app.modules.auth.password import hash_password
from app.modules.auth.tokens import create_access_token
from app.modules.organizations.constants import (
    OrganizationRole,
    OrganizationStatus,
    OrganizationType,
)
from app.modules.organizations.repository import (
    OrganizationMemberRepository,
    OrganizationRepository,
)
from sqlalchemy import select


def _create_user(
    db_session,
    *,
    global_role: GlobalRole = GlobalRole.USER,
) -> User:
    user = User(
        email=f"audit-{uuid4()}@example.com",
        password_hash=hash_password("SecurePass123!"),
        status=UserStatus.ACTIVE,
        global_role=global_role,
    )
    db_session.add(user)
    db_session.flush()
    return user


def _auth_header(user: User) -> dict[str, str]:
    token, _ = create_access_token(user, get_settings())
    return {"Authorization": f"Bearer {token}"}


def _create_org_with_owner(db_session, owner: User):
    org_repo = OrganizationRepository(db_session)
    member_repo = OrganizationMemberRepository(db_session)
    org = org_repo.create(
        name="Audit Org",
        slug=f"audit-org-{uuid4().hex[:8]}",
        org_type=OrganizationType.NIGHTCLUB,
        created_by_user_id=owner.id,
        status=OrganizationStatus.ACTIVE,
    )
    member_repo.add_member(
        user_id=owner.id,
        organization_id=org.id,
        role=OrganizationRole.OWNER,
    )
    return org


def _latest_audit(db_session, action: AuditAction) -> AuditLog:
    log = db_session.scalar(
        select(AuditLog)
        .where(AuditLog.action == action.value)
        .order_by(AuditLog.created_at.desc())
    )
    assert log is not None
    return log


def test_organization_suspended_constant_exists() -> None:
    assert AuditAction.ORGANIZATION_SUSPENDED.value == "organization_suspended"


def test_create_organization_audit_shape(auth_client, db_session) -> None:
    owner = _create_user(db_session)
    response = auth_client.post(
        "/api/organizations",
        json={
            "name": "Audit Create",
            "type": "nightclub",
            "city": "Paris",
            "country": "FR",
        },
        headers=_auth_header(owner),
    )
    org_id = response.json()["id"]
    log = _latest_audit(db_session, AuditAction.ORGANIZATION_CREATED)

    assert log.resource_type == "organization"
    assert log.resource_id == org_id
    assert log.actor_user_id == owner.id
    assert log.audit_metadata is not None
    assert log.audit_metadata["organization_id"] == org_id
    assert log.audit_metadata["actor_role"] == "owner"


def test_update_organization_audit_shape(auth_client, db_session) -> None:
    owner = _create_user(db_session)
    org = _create_org_with_owner(db_session, owner)

    auth_client.patch(
        f"/api/organizations/{org.id}",
        json={"description": "Audited update"},
        headers=_auth_header(owner),
    )
    log = _latest_audit(db_session, AuditAction.ORGANIZATION_UPDATED)

    assert log.resource_type == "organization"
    assert log.resource_id == str(org.id)
    assert log.audit_metadata is not None
    assert log.audit_metadata["organization_id"] == str(org.id)
    assert log.audit_metadata["actor_role"] == "owner"
    assert log.audit_metadata["updated_fields"] == ["description"]


def test_archive_organization_audit_shape(auth_client, db_session) -> None:
    owner = _create_user(db_session)
    org = _create_org_with_owner(db_session, owner)

    auth_client.delete(
        f"/api/organizations/{org.id}",
        headers=_auth_header(owner),
    )
    log = _latest_audit(db_session, AuditAction.ORGANIZATION_ARCHIVED)

    assert log.resource_type == "organization"
    assert log.resource_id == str(org.id)
    assert log.audit_metadata is not None
    assert log.audit_metadata["organization_id"] == str(org.id)
    assert log.audit_metadata["actor_role"] == "owner"
    assert log.audit_metadata["previous_status"] == "active"
    assert log.audit_metadata["new_status"] == "archived"


def test_member_add_audit_shape(auth_client, db_session) -> None:
    owner = _create_user(db_session)
    target = _create_user(db_session)
    org = _create_org_with_owner(db_session, owner)

    response = auth_client.post(
        f"/api/organizations/{org.id}/members",
        json={"user_id": str(target.id), "role": "staff"},
        headers=_auth_header(owner),
    )
    member_id = response.json()["id"]
    log = _latest_audit(db_session, AuditAction.ORGANIZATION_MEMBER_ADDED)

    assert log.resource_type == "organization_member"
    assert log.resource_id == member_id
    assert log.audit_metadata is not None
    assert log.audit_metadata["organization_id"] == str(org.id)
    assert log.audit_metadata["actor_role"] == "owner"
    assert log.audit_metadata["target_user_id"] == str(target.id)
    assert log.audit_metadata["role"] == "staff"


def test_member_role_update_audit_shape(auth_client, db_session) -> None:
    owner = _create_user(db_session)
    staff = _create_user(db_session)
    org = _create_org_with_owner(db_session, owner)
    member = OrganizationMemberRepository(db_session).add_member(
        user_id=staff.id,
        organization_id=org.id,
        role=OrganizationRole.STAFF,
    )

    auth_client.patch(
        f"/api/organizations/{org.id}/members/{member.id}",
        json={"role": "admin"},
        headers=_auth_header(owner),
    )
    log = _latest_audit(db_session, AuditAction.ORGANIZATION_MEMBER_ROLE_UPDATED)

    assert log.resource_type == "organization_member"
    assert log.resource_id == str(member.id)
    assert log.audit_metadata is not None
    assert log.audit_metadata["organization_id"] == str(org.id)
    assert log.audit_metadata["actor_role"] == "owner"
    assert log.audit_metadata["target_user_id"] == str(staff.id)
    assert log.audit_metadata["previous_role"] == "staff"
    assert log.audit_metadata["new_role"] == "admin"


def test_member_remove_audit_shape(auth_client, db_session) -> None:
    owner = _create_user(db_session)
    staff = _create_user(db_session)
    org = _create_org_with_owner(db_session, owner)
    member = OrganizationMemberRepository(db_session).add_member(
        user_id=staff.id,
        organization_id=org.id,
        role=OrganizationRole.STAFF,
    )

    auth_client.delete(
        f"/api/organizations/{org.id}/members/{member.id}",
        headers=_auth_header(owner),
    )
    log = _latest_audit(db_session, AuditAction.ORGANIZATION_MEMBER_REMOVED)

    assert log.resource_type == "organization_member"
    assert log.resource_id == str(member.id)
    assert log.audit_metadata is not None
    assert log.audit_metadata["organization_id"] == str(org.id)
    assert log.audit_metadata["actor_role"] == "owner"
    assert log.audit_metadata["target_user_id"] == str(staff.id)
    assert log.audit_metadata["previous_status"] == "active"
    assert log.audit_metadata["new_status"] == "left"
    assert log.audit_metadata["self_leave"] is False


def test_super_admin_bypass_audit_shape(auth_client, db_session) -> None:
    owner = _create_user(db_session)
    super_admin = _create_user(db_session, global_role=GlobalRole.SUPER_ADMIN)
    org = _create_org_with_owner(db_session, owner)

    auth_client.get(
        f"/api/organizations/{org.id}",
        headers=_auth_header(super_admin),
    )
    log = _latest_audit(db_session, AuditAction.ORGANIZATION_RBAC_SUPER_ADMIN_BYPASS)

    assert log.resource_type == "organization"
    assert log.resource_id == str(org.id)
    assert log.actor_user_id == super_admin.id
    assert log.audit_metadata is not None
    assert log.audit_metadata["organization_id"] == str(org.id)
    assert "requested_roles" in log.audit_metadata


def test_audit_metadata_sanitized(db_session) -> None:
    user = _create_user(db_session)
    service = AuditService(AuditRepository(db_session))
    log = service.record(
        AuditAction.ORGANIZATION_UPDATED.value,
        actor_user_id=user.id,
        resource_type="organization",
        resource_id=str(uuid4()),
        metadata={
            "organization_id": str(uuid4()),
            "actor_role": "owner",
            "password": "secret",
            "password_hash": "hash",
            "token": "tok",
            "jwt": "jwt-value",
            "safe_field": "ok",
        },
    )
    db_session.flush()

    assert log.audit_metadata is not None
    assert "password" not in log.audit_metadata
    assert "password_hash" not in log.audit_metadata
    assert "token" not in log.audit_metadata
    assert "jwt" not in log.audit_metadata
    assert log.audit_metadata["safe_field"] == "ok"


def test_no_sensitive_metadata_leakage_in_member_audit(auth_client, db_session) -> None:
    owner = _create_user(db_session)
    target = _create_user(db_session)
    org = _create_org_with_owner(db_session, owner)

    auth_client.post(
        f"/api/organizations/{org.id}/members",
        json={"user_id": str(target.id), "role": "viewer"},
        headers=_auth_header(owner),
    )
    log = _latest_audit(db_session, AuditAction.ORGANIZATION_MEMBER_ADDED)
    metadata = log.audit_metadata or {}

    for forbidden in ("password", "password_hash", "token", "jwt", "secret"):
        assert forbidden not in metadata


def test_member_audit_always_has_organization_id(auth_client, db_session) -> None:
    owner = _create_user(db_session)
    staff = _create_user(db_session)
    org = _create_org_with_owner(db_session, owner)
    member = OrganizationMemberRepository(db_session).add_member(
        user_id=staff.id,
        organization_id=org.id,
        role=OrganizationRole.VIEWER,
    )

    auth_client.delete(
        f"/api/organizations/{org.id}/members/{member.id}",
        headers=_auth_header(staff),
    )

    member_logs = db_session.scalars(
        select(AuditLog).where(
            AuditLog.resource_type == "organization_member",
            AuditLog.action == AuditAction.ORGANIZATION_MEMBER_REMOVED.value,
        )
    ).all()
    assert member_logs
    for log in member_logs:
        assert log.audit_metadata is not None
        assert log.audit_metadata.get("organization_id") == str(org.id)
