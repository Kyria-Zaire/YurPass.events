"""Organization RBAC tests — TICKET-007C."""

import inspect
from uuid import uuid4

import pytest
from app.modules.audit.constants import AuditAction
from app.modules.audit.models import AuditLog
from app.modules.auth.constants import GlobalRole, UserStatus
from app.modules.auth.models import User
from app.modules.auth.password import hash_password
from app.modules.organizations.constants import (
    MemberStatus,
    OrganizationRole,
    OrganizationStatus,
    OrganizationType,
)
from app.modules.organizations.models import OrganizationMember
from app.modules.organizations.permissions import (
    ORGANIZATION_ROLE_PERMISSIONS,
    OrgRoleAccess,
    SuperAdminOrgBypass,
    require_org_member,
    require_org_roles,
    role_has_permission,
)
from app.modules.organizations.repository import (
    OrganizationMemberRepository,
    OrganizationRepository,
)
from app.shared.exceptions import PermissionDeniedError
from sqlalchemy import func, select


def _create_user(
    db_session,
    *,
    global_role: GlobalRole = GlobalRole.USER,
) -> User:
    user = User(
        email=f"rbac-{uuid4()}@example.com",
        password_hash=hash_password("SecurePass123!"),
        status=UserStatus.ACTIVE,
        global_role=global_role,
    )
    db_session.add(user)
    db_session.flush()
    return user


def _create_organization(db_session, owner: User):
    return OrganizationRepository(db_session).create(
        name="RBAC Org",
        slug=f"rbac-org-{uuid4().hex[:8]}",
        org_type=OrganizationType.NIGHTCLUB,
        created_by_user_id=owner.id,
        status=OrganizationStatus.ACTIVE,
    )


def _add_member(
    db_session,
    *,
    user: User,
    organization_id,
    role: OrganizationRole,
    status: MemberStatus = MemberStatus.ACTIVE,
) -> OrganizationMember:
    return OrganizationMemberRepository(db_session).add_member(
        user_id=user.id,
        organization_id=organization_id,
        role=role,
        status=status,
    )


def test_owner_permission_matrix() -> None:
    owner_permissions = set(ORGANIZATION_ROLE_PERMISSIONS[OrganizationRole.OWNER])
    assert owner_permissions == {
        "organization:read",
        "organization:update",
        "organization:archive",
        "member:read",
        "member:add",
        "member:update_role",
        "member:remove",
    }
    for permission in owner_permissions:
        assert role_has_permission(OrganizationRole.OWNER, permission)


def test_admin_permission_matrix() -> None:
    assert role_has_permission(OrganizationRole.ADMIN, "organization:read")
    assert role_has_permission(OrganizationRole.ADMIN, "organization:update")
    assert role_has_permission(OrganizationRole.ADMIN, "member:read")
    assert role_has_permission(OrganizationRole.ADMIN, "member:add")
    assert not role_has_permission(OrganizationRole.ADMIN, "organization:archive")
    assert not role_has_permission(OrganizationRole.ADMIN, "member:remove")


def test_staff_permission_matrix() -> None:
    assert role_has_permission(OrganizationRole.STAFF, "organization:read")
    assert role_has_permission(OrganizationRole.STAFF, "member:read")
    assert not role_has_permission(OrganizationRole.STAFF, "organization:update")
    assert not role_has_permission(OrganizationRole.STAFF, "member:add")


def test_viewer_permission_matrix() -> None:
    assert role_has_permission(OrganizationRole.VIEWER, "organization:read")
    assert not role_has_permission(OrganizationRole.VIEWER, "member:read")
    assert not role_has_permission(OrganizationRole.VIEWER, "organization:update")


def test_role_has_permission_unknown_permission() -> None:
    assert not role_has_permission(OrganizationRole.VIEWER, "organization:delete")


def test_require_org_roles_typed_with_organization_role() -> None:
    signature = inspect.signature(require_org_roles)
    assert signature.parameters["allowed_roles"].annotation is OrganizationRole


def test_require_org_member_allows_active_member(db_session) -> None:
    owner = _create_user(db_session)
    organization = _create_organization(db_session, owner)
    member = _add_member(
        db_session,
        user=owner,
        organization_id=organization.id,
        role=OrganizationRole.OWNER,
    )

    resolved = require_org_member(
        organization_id=organization.id,
        user=owner,
        db=db_session,
    )
    assert resolved.id == member.id
    assert resolved.status == MemberStatus.ACTIVE


def test_require_org_member_rejects_non_member(db_session) -> None:
    owner = _create_user(db_session)
    outsider = _create_user(db_session)
    organization = _create_organization(db_session, owner)

    with pytest.raises(PermissionDeniedError):
        require_org_member(
            organization_id=organization.id,
            user=outsider,
            db=db_session,
        )


def test_require_org_member_rejects_suspended_member(db_session) -> None:
    owner = _create_user(db_session)
    organization = _create_organization(db_session, owner)
    _add_member(
        db_session,
        user=owner,
        organization_id=organization.id,
        role=OrganizationRole.ADMIN,
        status=MemberStatus.SUSPENDED,
    )

    with pytest.raises(PermissionDeniedError):
        require_org_member(
            organization_id=organization.id,
            user=owner,
            db=db_session,
        )


def test_require_org_member_rejects_left_member(db_session) -> None:
    owner = _create_user(db_session)
    organization = _create_organization(db_session, owner)
    _add_member(
        db_session,
        user=owner,
        organization_id=organization.id,
        role=OrganizationRole.ADMIN,
        status=MemberStatus.LEFT,
    )

    with pytest.raises(PermissionDeniedError):
        require_org_member(
            organization_id=organization.id,
            user=owner,
            db=db_session,
        )


def test_require_org_roles_allows_matching_role(db_session) -> None:
    owner = _create_user(db_session)
    organization = _create_organization(db_session, owner)
    member = _add_member(
        db_session,
        user=owner,
        organization_id=organization.id,
        role=OrganizationRole.OWNER,
    )

    guard = require_org_roles(OrganizationRole.OWNER, OrganizationRole.ADMIN)
    access = guard(
        organization_id=organization.id,
        user=owner,
        db=db_session,
    )

    assert isinstance(access, OrgRoleAccess)
    assert access.member is not None
    assert access.member.id == member.id
    assert access.is_super_admin_bypass is False


def test_require_org_roles_rejects_unauthorized_role(db_session) -> None:
    owner = _create_user(db_session)
    organization = _create_organization(db_session, owner)
    _add_member(
        db_session,
        user=owner,
        organization_id=organization.id,
        role=OrganizationRole.VIEWER,
    )

    guard = require_org_roles(OrganizationRole.OWNER, OrganizationRole.ADMIN)
    with pytest.raises(PermissionDeniedError):
        guard(
            organization_id=organization.id,
            user=owner,
            db=db_session,
        )


def test_require_org_roles_rejects_non_member(db_session) -> None:
    owner = _create_user(db_session)
    outsider = _create_user(db_session)
    organization = _create_organization(db_session, owner)

    guard = require_org_roles(OrganizationRole.VIEWER)
    with pytest.raises(PermissionDeniedError):
        guard(
            organization_id=organization.id,
            user=outsider,
            db=db_session,
        )


def test_super_admin_bypass_without_membership(db_session) -> None:
    owner = _create_user(db_session)
    super_admin = _create_user(db_session, global_role=GlobalRole.SUPER_ADMIN)
    organization = _create_organization(db_session, owner)

    guard = require_org_roles(OrganizationRole.OWNER)
    access = guard(
        organization_id=organization.id,
        user=super_admin,
        db=db_session,
    )

    assert isinstance(access, SuperAdminOrgBypass)
    assert access.user.id == super_admin.id
    assert access.organization_id == organization.id


def test_super_admin_bypass_is_audited(db_session) -> None:
    owner = _create_user(db_session)
    super_admin = _create_user(db_session, global_role=GlobalRole.SUPER_ADMIN)
    organization = _create_organization(db_session, owner)

    guard = require_org_roles(OrganizationRole.ADMIN, OrganizationRole.OWNER)
    guard(
        organization_id=organization.id,
        user=super_admin,
        db=db_session,
    )

    logs = list(
        db_session.scalars(
            select(AuditLog).where(
                AuditLog.action == AuditAction.ORGANIZATION_RBAC_SUPER_ADMIN_BYPASS.value
            )
        )
    )
    assert len(logs) == 1
    assert logs[0].actor_user_id == super_admin.id
    assert logs[0].resource_id == str(organization.id)
    assert logs[0].audit_metadata is not None
    assert logs[0].audit_metadata["requested_roles"] == ["admin", "owner"]


def test_super_admin_bypass_does_not_create_member_row(db_session) -> None:
    owner = _create_user(db_session)
    super_admin = _create_user(db_session, global_role=GlobalRole.SUPER_ADMIN)
    organization = _create_organization(db_session, owner)

    before = db_session.scalar(select(func.count()).select_from(OrganizationMember))
    guard = require_org_roles(OrganizationRole.OWNER)
    guard(
        organization_id=organization.id,
        user=super_admin,
        db=db_session,
    )
    after = db_session.scalar(select(func.count()).select_from(OrganizationMember))

    assert before == after
    assert (
        OrganizationMemberRepository(db_session).get_member(super_admin.id, organization.id)
        is None
    )


def test_no_organization_members_endpoints_exposed() -> None:
    from app.main import app

    member_paths = [
        route.path
        for route in app.routes
        if "/api/organizations" in getattr(route, "path", "")
        and "/members" in getattr(route, "path", "")
    ]
    assert member_paths == []
