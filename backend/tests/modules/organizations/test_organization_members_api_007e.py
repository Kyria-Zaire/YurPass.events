"""Organization members API tests — TICKET-007E."""

from uuid import uuid4

from app.core.config import get_settings
from app.modules.audit.constants import AuditAction
from app.modules.audit.models import AuditLog
from app.modules.auth.constants import GlobalRole, UserStatus
from app.modules.auth.models import User
from app.modules.auth.password import hash_password
from app.modules.auth.tokens import create_access_token
from app.modules.organizations.constants import (
    MemberStatus,
    OrganizationRole,
    OrganizationStatus,
    OrganizationType,
)
from app.modules.organizations.repository import (
    OrganizationMemberRepository,
    OrganizationRepository,
)
from sqlalchemy import func, select


def _create_user(
    db_session,
    *,
    global_role: GlobalRole = GlobalRole.USER,
) -> User:
    user = User(
        email=f"members-{uuid4()}@example.com",
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
        name="Members Org",
        slug=f"members-org-{uuid4().hex[:8]}",
        org_type=OrganizationType.NIGHTCLUB,
        created_by_user_id=owner.id,
        status=OrganizationStatus.ACTIVE,
    )
    owner_member = member_repo.add_member(
        user_id=owner.id,
        organization_id=org.id,
        role=OrganizationRole.OWNER,
    )
    return org, owner_member


def _add_member(
    db_session,
    *,
    user: User,
    organization_id,
    role: OrganizationRole,
    status: MemberStatus = MemberStatus.ACTIVE,
):
    return OrganizationMemberRepository(db_session).add_member(
        user_id=user.id,
        organization_id=organization_id,
        role=role,
        status=status,
    )


def _members_url(org_id) -> str:
    return f"/api/organizations/{org_id}/members"


def _member_url(org_id, member_id) -> str:
    return f"/api/organizations/{org_id}/members/{member_id}"


def test_get_members_owner_admin_staff_ok(auth_client, db_session) -> None:
    owner = _create_user(db_session)
    admin = _create_user(db_session)
    staff = _create_user(db_session)
    org, _ = _create_org_with_owner(db_session, owner)
    _add_member(db_session, user=admin, organization_id=org.id, role=OrganizationRole.ADMIN)
    _add_member(db_session, user=staff, organization_id=org.id, role=OrganizationRole.STAFF)

    for actor in (owner, admin, staff):
        response = auth_client.get(_members_url(org.id), headers=_auth_header(actor))
        assert response.status_code == 200
        members = response.json()["members"]
        assert len(members) == 3
        assert all(member["status"] == "active" for member in members)


def test_get_members_viewer_refused(auth_client, db_session) -> None:
    owner = _create_user(db_session)
    viewer = _create_user(db_session)
    org, _ = _create_org_with_owner(db_session, owner)
    _add_member(db_session, user=viewer, organization_id=org.id, role=OrganizationRole.VIEWER)

    response = auth_client.get(_members_url(org.id), headers=_auth_header(viewer))
    assert response.status_code == 403


def test_get_members_include_inactive_owner_only(auth_client, db_session) -> None:
    owner = _create_user(db_session)
    admin = _create_user(db_session)
    left_user = _create_user(db_session)
    org, _ = _create_org_with_owner(db_session, owner)
    _add_member(db_session, user=admin, organization_id=org.id, role=OrganizationRole.ADMIN)
    _add_member(
        db_session,
        user=left_user,
        organization_id=org.id,
        role=OrganizationRole.STAFF,
        status=MemberStatus.LEFT,
    )

    owner_response = auth_client.get(
        _members_url(org.id),
        params={"include_inactive": "true"},
        headers=_auth_header(owner),
    )
    assert owner_response.status_code == 200
    assert len(owner_response.json()["members"]) == 3

    admin_response = auth_client.get(
        _members_url(org.id),
        params={"include_inactive": "true"},
        headers=_auth_header(admin),
    )
    assert admin_response.status_code == 403


def test_post_member_owner_admin_ok(auth_client, db_session) -> None:
    owner = _create_user(db_session)
    admin = _create_user(db_session)
    org, _ = _create_org_with_owner(db_session, owner)
    _add_member(db_session, user=admin, organization_id=org.id, role=OrganizationRole.ADMIN)

    for actor in (owner, admin):
        new_target = _create_user(db_session)
        response = auth_client.post(
            _members_url(org.id),
            json={"user_id": str(new_target.id), "role": "staff"},
            headers=_auth_header(actor),
        )
        assert response.status_code == 201
        assert response.json()["role"] == "staff"
        assert response.json()["status"] == "active"


def test_post_member_viewer_staff_refused(auth_client, db_session) -> None:
    owner = _create_user(db_session)
    staff = _create_user(db_session)
    viewer = _create_user(db_session)
    target = _create_user(db_session)
    org, _ = _create_org_with_owner(db_session, owner)
    _add_member(db_session, user=staff, organization_id=org.id, role=OrganizationRole.STAFF)
    _add_member(db_session, user=viewer, organization_id=org.id, role=OrganizationRole.VIEWER)

    for actor in (staff, viewer):
        response = auth_client.post(
            _members_url(org.id),
            json={"user_id": str(target.id), "role": "viewer"},
            headers=_auth_header(actor),
        )
        assert response.status_code == 403


def test_post_member_unknown_user_refused(auth_client, db_session) -> None:
    owner = _create_user(db_session)
    org, _ = _create_org_with_owner(db_session, owner)

    response = auth_client.post(
        _members_url(org.id),
        json={"user_id": str(uuid4()), "role": "staff"},
        headers=_auth_header(owner),
    )
    assert response.status_code == 404


def test_post_member_duplicate_refused(auth_client, db_session) -> None:
    owner = _create_user(db_session)
    existing = _create_user(db_session)
    org, _ = _create_org_with_owner(db_session, owner)
    _add_member(db_session, user=existing, organization_id=org.id, role=OrganizationRole.STAFF)

    response = auth_client.post(
        _members_url(org.id),
        json={"user_id": str(existing.id), "role": "viewer"},
        headers=_auth_header(owner),
    )
    assert response.status_code == 409
    assert response.json()["code"] == "member_already_exists"


def test_post_member_inactive_refused(auth_client, db_session) -> None:
    owner = _create_user(db_session)
    inactive = _create_user(db_session)
    org, _ = _create_org_with_owner(db_session, owner)
    _add_member(
        db_session,
        user=inactive,
        organization_id=org.id,
        role=OrganizationRole.STAFF,
        status=MemberStatus.LEFT,
    )

    response = auth_client.post(
        _members_url(org.id),
        json={"user_id": str(inactive.id), "role": "viewer"},
        headers=_auth_header(owner),
    )
    assert response.status_code == 409
    assert response.json()["code"] == "member_inactive_requires_manual_reactivation"


def test_post_member_owner_role_refused(auth_client, db_session) -> None:
    owner = _create_user(db_session)
    target = _create_user(db_session)
    org, _ = _create_org_with_owner(db_session, owner)

    response = auth_client.post(
        _members_url(org.id),
        json={"user_id": str(target.id), "role": "owner"},
        headers=_auth_header(owner),
    )
    assert response.status_code == 409
    assert response.json()["code"] == "owner_role_not_allowed"


def test_patch_role_owner_ok(auth_client, db_session) -> None:
    owner = _create_user(db_session)
    staff = _create_user(db_session)
    org, _ = _create_org_with_owner(db_session, owner)
    member = _add_member(
        db_session,
        user=staff,
        organization_id=org.id,
        role=OrganizationRole.STAFF,
    )

    response = auth_client.patch(
        _member_url(org.id, member.id),
        json={"role": "admin"},
        headers=_auth_header(owner),
    )
    assert response.status_code == 200
    assert response.json()["role"] == "admin"


def test_patch_role_admin_refused(auth_client, db_session) -> None:
    owner = _create_user(db_session)
    admin = _create_user(db_session)
    staff = _create_user(db_session)
    org, _ = _create_org_with_owner(db_session, owner)
    _add_member(db_session, user=admin, organization_id=org.id, role=OrganizationRole.ADMIN)
    member = _add_member(
        db_session,
        user=staff,
        organization_id=org.id,
        role=OrganizationRole.STAFF,
    )

    response = auth_client.patch(
        _member_url(org.id, member.id),
        json={"role": "viewer"},
        headers=_auth_header(admin),
    )
    assert response.status_code == 403


def test_patch_role_to_owner_refused(auth_client, db_session) -> None:
    owner = _create_user(db_session)
    staff = _create_user(db_session)
    org, _ = _create_org_with_owner(db_session, owner)
    member = _add_member(
        db_session,
        user=staff,
        organization_id=org.id,
        role=OrganizationRole.STAFF,
    )

    response = auth_client.patch(
        _member_url(org.id, member.id),
        json={"role": "owner"},
        headers=_auth_header(owner),
    )
    assert response.status_code == 409
    assert response.json()["code"] == "owner_role_not_allowed"


def test_delete_member_owner_ok_status_left(auth_client, db_session) -> None:
    owner = _create_user(db_session)
    staff = _create_user(db_session)
    org, _ = _create_org_with_owner(db_session, owner)
    member = _add_member(
        db_session,
        user=staff,
        organization_id=org.id,
        role=OrganizationRole.STAFF,
    )

    response = auth_client.delete(
        _member_url(org.id, member.id),
        headers=_auth_header(owner),
    )
    assert response.status_code == 200
    assert response.json()["status"] == "left"

    persisted = OrganizationMemberRepository(db_session).get_member_by_id(member.id)
    assert persisted is not None
    assert persisted.status == MemberStatus.LEFT


def test_delete_member_admin_refused(auth_client, db_session) -> None:
    owner = _create_user(db_session)
    admin = _create_user(db_session)
    staff = _create_user(db_session)
    org, _ = _create_org_with_owner(db_session, owner)
    _add_member(db_session, user=admin, organization_id=org.id, role=OrganizationRole.ADMIN)
    member = _add_member(
        db_session,
        user=staff,
        organization_id=org.id,
        role=OrganizationRole.STAFF,
    )

    response = auth_client.delete(
        _member_url(org.id, member.id),
        headers=_auth_header(admin),
    )
    assert response.status_code == 403


def test_self_leave_admin_staff_viewer_ok(auth_client, db_session) -> None:
    owner = _create_user(db_session)
    org, _ = _create_org_with_owner(db_session, owner)

    for role in (OrganizationRole.ADMIN, OrganizationRole.STAFF, OrganizationRole.VIEWER):
        user = _create_user(db_session)
        member = _add_member(db_session, user=user, organization_id=org.id, role=role)
        response = auth_client.delete(
            _member_url(org.id, member.id),
            headers=_auth_header(user),
        )
        assert response.status_code == 200
        assert response.json()["status"] == "left"


def test_self_leave_owner_refused_even_with_multiple_owners(auth_client, db_session) -> None:
    owner_a = _create_user(db_session)
    owner_b = _create_user(db_session)
    org, owner_a_member = _create_org_with_owner(db_session, owner_a)
    owner_b_member = _add_member(
        db_session,
        user=owner_b,
        organization_id=org.id,
        role=OrganizationRole.OWNER,
    )

    for member, actor in ((owner_a_member, owner_a), (owner_b_member, owner_b)):
        response = auth_client.delete(
            _member_url(org.id, member.id),
            headers=_auth_header(actor),
        )
        assert response.status_code == 403
        assert response.json()["code"] == "owner_self_leave_forbidden"


def test_remove_last_owner_refused(auth_client, db_session) -> None:
    owner = _create_user(db_session)
    super_admin = _create_user(db_session, global_role=GlobalRole.SUPER_ADMIN)
    org, owner_member = _create_org_with_owner(db_session, owner)

    response = auth_client.delete(
        _member_url(org.id, owner_member.id),
        headers=_auth_header(super_admin),
    )
    assert response.status_code == 409
    assert response.json()["code"] == "last_owner_protected"


def test_patch_last_owner_refused(auth_client, db_session) -> None:
    owner = _create_user(db_session)
    org, owner_member = _create_org_with_owner(db_session, owner)

    response = auth_client.patch(
        _member_url(org.id, owner_member.id),
        json={"role": "admin"},
        headers=_auth_header(owner),
    )
    assert response.status_code == 409
    assert response.json()["code"] == "last_owner_protected"


def test_audit_add_update_remove(auth_client, db_session) -> None:
    owner = _create_user(db_session)
    staff = _create_user(db_session)
    org, _ = _create_org_with_owner(db_session, owner)

    add_response = auth_client.post(
        _members_url(org.id),
        json={"user_id": str(staff.id), "role": "staff"},
        headers=_auth_header(owner),
    )
    member_id = add_response.json()["id"]

    auth_client.patch(
        _member_url(org.id, member_id),
        json={"role": "viewer"},
        headers=_auth_header(owner),
    )
    auth_client.delete(_member_url(org.id, member_id), headers=_auth_header(owner))

    actions = {
        row.action
        for row in db_session.scalars(
            select(AuditLog).where(
                AuditLog.resource_type == "organization_member",
            )
        )
    }
    assert AuditAction.ORGANIZATION_MEMBER_ADDED.value in actions
    assert AuditAction.ORGANIZATION_MEMBER_ROLE_UPDATED.value in actions
    assert AuditAction.ORGANIZATION_MEMBER_REMOVED.value in actions


def test_super_admin_bypass_list_and_remove_audited(auth_client, db_session) -> None:
    owner = _create_user(db_session)
    staff = _create_user(db_session)
    super_admin = _create_user(db_session, global_role=GlobalRole.SUPER_ADMIN)
    org, _ = _create_org_with_owner(db_session, owner)
    member = _add_member(
        db_session,
        user=staff,
        organization_id=org.id,
        role=OrganizationRole.STAFF,
    )

    list_response = auth_client.get(
        _members_url(org.id),
        headers=_auth_header(super_admin),
    )
    assert list_response.status_code == 200

    delete_response = auth_client.delete(
        _member_url(org.id, member.id),
        headers=_auth_header(super_admin),
    )
    assert delete_response.status_code == 200

    bypass_count = db_session.scalar(
        select(func.count())
        .select_from(AuditLog)
        .where(AuditLog.action == AuditAction.ORGANIZATION_RBAC_SUPER_ADMIN_BYPASS.value)
    )
    assert bypass_count >= 2


def test_no_physical_delete(auth_client, db_session) -> None:
    from app.modules.organizations.models import OrganizationMember

    owner = _create_user(db_session)
    staff = _create_user(db_session)
    org, _ = _create_org_with_owner(db_session, owner)
    member = _add_member(
        db_session,
        user=staff,
        organization_id=org.id,
        role=OrganizationRole.STAFF,
    )

    auth_client.delete(_member_url(org.id, member.id), headers=_auth_header(owner))

    count = db_session.scalar(select(func.count()).select_from(OrganizationMember))
    assert count == 2
    persisted = db_session.get(OrganizationMember, member.id)
    assert persisted is not None
    assert persisted.status == MemberStatus.LEFT


def test_no_user_creation_on_post(auth_client, db_session) -> None:
    owner = _create_user(db_session)
    target = _create_user(db_session)
    org, _ = _create_org_with_owner(db_session, owner)

    before = db_session.scalar(select(func.count()).select_from(User))

    auth_client.post(
        _members_url(org.id),
        json={"user_id": str(target.id), "role": "viewer"},
        headers=_auth_header(owner),
    )

    after = db_session.scalar(select(func.count()).select_from(User))
    assert before == after


def test_only_four_member_endpoints_exposed() -> None:
    from app.main import app

    member_paths = [
        route.path
        for route in app.routes
        if "/api/organizations" in getattr(route, "path", "")
        and "/members" in getattr(route, "path", "")
    ]
    assert set(member_paths) == {
        "/api/organizations/{organization_id}/members",
        "/api/organizations/{organization_id}/members/{member_id}",
    }
    assert len(member_paths) == 4
