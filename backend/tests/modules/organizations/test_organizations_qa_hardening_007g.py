"""Organizations QA hardening — TICKET-007G feature closeout."""

from uuid import uuid4

import pytest
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
from app.modules.organizations.models import Organization, OrganizationMember
from app.modules.organizations.repository import (
    OrganizationMemberRepository,
    OrganizationRepository,
)
from app.modules.organizations.slug import slugify_name
from sqlalchemy import func, inspect, select, text
from sqlalchemy.exc import IntegrityError


def _create_user(
    db_session,
    *,
    global_role: GlobalRole = GlobalRole.USER,
) -> User:
    user = User(
        email=f"qa-{uuid4()}@example.com",
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


def _org_payload(name: str = "QA Club") -> dict:
    return {
        "name": name,
        "type": "nightclub",
        "city": "Paris",
        "country": "FR",
    }


def _setup_org_with_roles(db_session, *, include_viewer: bool = True):
    owner = _create_user(db_session)
    admin = _create_user(db_session)
    staff = _create_user(db_session)
    viewer = _create_user(db_session) if include_viewer else None
    org_repo = OrganizationRepository(db_session)
    member_repo = OrganizationMemberRepository(db_session)

    org = org_repo.create(
        name="QA Matrix Org",
        slug=f"qa-matrix-{uuid4().hex[:8]}",
        org_type=OrganizationType.NIGHTCLUB,
        created_by_user_id=owner.id,
        status=OrganizationStatus.ACTIVE,
    )
    member_repo.add_member(user_id=owner.id, organization_id=org.id, role=OrganizationRole.OWNER)
    member_repo.add_member(user_id=admin.id, organization_id=org.id, role=OrganizationRole.ADMIN)
    member_repo.add_member(user_id=staff.id, organization_id=org.id, role=OrganizationRole.STAFF)
    if viewer is not None:
        member_repo.add_member(
            user_id=viewer.id,
            organization_id=org.id,
            role=OrganizationRole.VIEWER,
        )
    staff_member = member_repo.get_member(staff.id, org.id)
    assert staff_member is not None
    return owner, admin, staff, viewer, org, staff_member


# --- DB constraints (CTO) ---


def test_db_constraint_uq_organization_members_user_org(db_engine) -> None:
    inspector = inspect(db_engine)
    uniques = inspector.get_unique_constraints("organization_members")
    assert any(c["name"] == "uq_organization_members_user_org" for c in uniques)


def test_db_constraint_uq_organizations_slug(db_engine) -> None:
    inspector = inspect(db_engine)
    indexes = inspector.get_indexes("organizations")
    slug_indexes = [idx for idx in indexes if "slug" in idx.get("column_names", [])]
    assert slug_indexes
    assert any(idx.get("unique") for idx in slug_indexes)


def test_db_constraint_fk_organization_members_organization_id(db_engine) -> None:
    inspector = inspect(db_engine)
    fks = inspector.get_foreign_keys("organization_members")
    assert any(
        fk["referred_table"] == "organizations" and fk["referred_columns"] == ["id"]
        for fk in fks
    )


def test_db_constraint_fk_organization_members_user_id(db_engine) -> None:
    inspector = inspect(db_engine)
    fks = inspector.get_foreign_keys("organization_members")
    assert any(
        fk["referred_table"] == "users" and fk["referred_columns"] == ["id"] for fk in fks
    )


def test_fk_organization_members_user_id_enforced(db_session) -> None:
    owner = _create_user(db_session)
    org = OrganizationRepository(db_session).create(
        name="FK User Org",
        slug=f"fk-user-{uuid4().hex[:8]}",
        org_type=OrganizationType.NIGHTCLUB,
        created_by_user_id=owner.id,
    )
    with pytest.raises(IntegrityError):
        OrganizationMemberRepository(db_session).add_member(
            user_id=uuid4(),
            organization_id=org.id,
            role=OrganizationRole.STAFF,
        )


def test_alembic_head_schema_organizations_tables(db_engine) -> None:
    inspector = inspect(db_engine)
    assert inspector.has_table("organizations")
    assert inspector.has_table("organization_members")
    with db_engine.connect() as connection:
        result = connection.execute(
            text(
                "SELECT typname FROM pg_type WHERE typname IN "
                "('organization_type', 'organization_status', "
                "'organization_role', 'member_status')"
            )
        )
        enums = {row[0] for row in result}
    assert enums == {
        "organization_type",
        "organization_status",
        "organization_role",
        "member_status",
    }


# --- RBAC matrix ---


def test_owner_full_access_matrix(auth_client, db_session) -> None:
    owner, admin, staff, _viewer, org, staff_member = _setup_org_with_roles(db_session)
    target = _create_user(db_session)
    org_url = f"/api/organizations/{org.id}"
    members_url = f"{org_url}/members"

    assert auth_client.get(org_url, headers=_auth_header(owner)).status_code == 200
    assert auth_client.patch(
        org_url, json={"description": "ok"}, headers=_auth_header(owner)
    ).status_code == 200
    assert auth_client.get(members_url, headers=_auth_header(owner)).status_code == 200
    add = auth_client.post(
        members_url,
        json={"user_id": str(target.id), "role": "viewer"},
        headers=_auth_header(owner),
    )
    assert add.status_code == 201
    member_id = add.json()["id"]
    assert auth_client.patch(
        f"{members_url}/{member_id}",
        json={"role": "staff"},
        headers=_auth_header(owner),
    ).status_code == 200
    assert auth_client.delete(
        f"{members_url}/{member_id}",
        headers=_auth_header(owner),
    ).status_code == 200
    assert auth_client.delete(
        f"{members_url}/{staff_member.id}",
        headers=_auth_header(owner),
    ).status_code == 200


def test_admin_allowed_and_denied(auth_client, db_session) -> None:
    owner, admin, _staff, _viewer, org, staff_member = _setup_org_with_roles(db_session)
    target = _create_user(db_session)
    org_url = f"/api/organizations/{org.id}"
    members_url = f"{org_url}/members"

    assert auth_client.patch(
        org_url, json={"city": "Lyon"}, headers=_auth_header(admin)
    ).status_code == 200
    assert auth_client.get(members_url, headers=_auth_header(admin)).status_code == 200
    assert auth_client.post(
        members_url,
        json={"user_id": str(target.id), "role": "viewer"},
        headers=_auth_header(admin),
    ).status_code == 201
    assert auth_client.delete(org_url, headers=_auth_header(admin)).status_code == 403
    assert auth_client.patch(
        f"{members_url}/{staff_member.id}",
        json={"role": "viewer"},
        headers=_auth_header(admin),
    ).status_code == 403
    assert auth_client.delete(
        f"{members_url}/{staff_member.id}",
        headers=_auth_header(admin),
    ).status_code == 403


def test_staff_allowed_and_denied(auth_client, db_session) -> None:
    _owner, _admin, staff, _viewer, org, _staff_member = _setup_org_with_roles(db_session)
    org_url = f"/api/organizations/{org.id}"
    members_url = f"{org_url}/members"
    target = _create_user(db_session)

    assert auth_client.get(org_url, headers=_auth_header(staff)).status_code == 200
    assert auth_client.get(members_url, headers=_auth_header(staff)).status_code == 200
    assert auth_client.patch(
        org_url, json={"description": "nope"}, headers=_auth_header(staff)
    ).status_code == 403
    assert auth_client.post(
        members_url,
        json={"user_id": str(target.id), "role": "viewer"},
        headers=_auth_header(staff),
    ).status_code == 403


def test_viewer_allowed_and_denied(auth_client, db_session) -> None:
    _owner, _admin, _staff, viewer, org, _staff_member = _setup_org_with_roles(db_session)
    org_url = f"/api/organizations/{org.id}"
    members_url = f"{org_url}/members"

    assert auth_client.get(org_url, headers=_auth_header(viewer)).status_code == 200
    assert auth_client.get(members_url, headers=_auth_header(viewer)).status_code == 403


def test_non_member_denied_org_routes(auth_client, db_session) -> None:
    owner = _create_user(db_session)
    outsider = _create_user(db_session)
    org = OrganizationRepository(db_session).create(
        name="Private Org",
        slug=f"private-{uuid4().hex[:8]}",
        org_type=OrganizationType.NIGHTCLUB,
        created_by_user_id=owner.id,
        status=OrganizationStatus.ACTIVE,
    )
    OrganizationMemberRepository(db_session).add_member(
        user_id=owner.id,
        organization_id=org.id,
        role=OrganizationRole.OWNER,
    )
    staff = _create_user(db_session)
    member = OrganizationMemberRepository(db_session).add_member(
        user_id=staff.id,
        organization_id=org.id,
        role=OrganizationRole.STAFF,
    )

    org_url = f"/api/organizations/{org.id}"
    members_url = f"{org_url}/members"
    assert auth_client.get(org_url, headers=_auth_header(outsider)).status_code == 403
    assert auth_client.patch(
        org_url, json={"description": "x"}, headers=_auth_header(outsider)
    ).status_code == 403
    assert auth_client.delete(org_url, headers=_auth_header(outsider)).status_code == 403
    assert auth_client.get(members_url, headers=_auth_header(outsider)).status_code == 403
    assert auth_client.post(
        members_url,
        json={"user_id": str(outsider.id), "role": "viewer"},
        headers=_auth_header(outsider),
    ).status_code == 403
    assert auth_client.patch(
        f"{members_url}/{member.id}",
        json={"role": "viewer"},
        headers=_auth_header(outsider),
    ).status_code == 403
    assert auth_client.delete(
        f"{members_url}/{member.id}",
        headers=_auth_header(outsider),
    ).status_code == 403


def test_suspended_member_denied(auth_client, db_session) -> None:
    owner = _create_user(db_session)
    suspended_user = _create_user(db_session)
    org = OrganizationRepository(db_session).create(
        name="Suspended Org",
        slug=f"susp-{uuid4().hex[:8]}",
        org_type=OrganizationType.NIGHTCLUB,
        created_by_user_id=owner.id,
        status=OrganizationStatus.ACTIVE,
    )
    repo = OrganizationMemberRepository(db_session)
    repo.add_member(user_id=owner.id, organization_id=org.id, role=OrganizationRole.OWNER)
    suspended = repo.add_member(
        user_id=suspended_user.id,
        organization_id=org.id,
        role=OrganizationRole.STAFF,
    )
    repo.update_member_status(suspended, MemberStatus.SUSPENDED)

    org_url = f"/api/organizations/{org.id}"
    assert auth_client.get(org_url, headers=_auth_header(suspended_user)).status_code == 403


def test_left_member_denied(auth_client, db_session) -> None:
    owner = _create_user(db_session)
    left_user = _create_user(db_session)
    org = OrganizationRepository(db_session).create(
        name="Left Org",
        slug=f"left-{uuid4().hex[:8]}",
        org_type=OrganizationType.NIGHTCLUB,
        created_by_user_id=owner.id,
        status=OrganizationStatus.ACTIVE,
    )
    repo = OrganizationMemberRepository(db_session)
    repo.add_member(user_id=owner.id, organization_id=org.id, role=OrganizationRole.OWNER)
    left_member = repo.add_member(
        user_id=left_user.id,
        organization_id=org.id,
        role=OrganizationRole.VIEWER,
    )
    repo.update_member_status(left_member, MemberStatus.LEFT)

    org_url = f"/api/organizations/{org.id}"
    assert auth_client.get(org_url, headers=_auth_header(left_user)).status_code == 403


def test_super_admin_bypass_audited_on_org_routes(auth_client, db_session) -> None:
    owner = _create_user(db_session)
    super_admin = _create_user(db_session, global_role=GlobalRole.SUPER_ADMIN)
    org = OrganizationRepository(db_session).create(
        name="Bypass Org",
        slug=f"bypass-{uuid4().hex[:8]}",
        org_type=OrganizationType.NIGHTCLUB,
        created_by_user_id=owner.id,
        status=OrganizationStatus.ACTIVE,
    )
    OrganizationMemberRepository(db_session).add_member(
        user_id=owner.id,
        organization_id=org.id,
        role=OrganizationRole.OWNER,
    )

    before = db_session.scalar(
        select(func.count())
        .select_from(AuditLog)
        .where(AuditLog.action == AuditAction.ORGANIZATION_RBAC_SUPER_ADMIN_BYPASS.value)
    )
    response = auth_client.get(
        f"/api/organizations/{org.id}",
        headers=_auth_header(super_admin),
    )
    assert response.status_code == 200
    after = db_session.scalar(
        select(func.count())
        .select_from(AuditLog)
        .where(AuditLog.action == AuditAction.ORGANIZATION_RBAC_SUPER_ADMIN_BYPASS.value)
    )
    assert after > before


# --- Ownership ---


def test_owner_auto_on_create(auth_client, db_session) -> None:
    user = _create_user(db_session)
    response = auth_client.post(
        "/api/organizations",
        json=_org_payload("Auto Owner"),
        headers=_auth_header(user),
    )
    org_id = response.json()["id"]
    member = OrganizationMemberRepository(db_session).get_member(user.id, org_id)
    assert member is not None
    assert member.role == OrganizationRole.OWNER
    assert member.status == MemberStatus.ACTIVE
    assert (
        OrganizationMemberRepository(db_session).count_active_owners(org_id) >= 1
    )


def test_no_owner_via_member_post(auth_client, db_session) -> None:
    owner = _create_user(db_session)
    target = _create_user(db_session)
    org = OrganizationRepository(db_session).create(
        name="No Owner Post",
        slug=f"no-owner-post-{uuid4().hex[:8]}",
        org_type=OrganizationType.NIGHTCLUB,
        created_by_user_id=owner.id,
        status=OrganizationStatus.ACTIVE,
    )
    OrganizationMemberRepository(db_session).add_member(
        user_id=owner.id,
        organization_id=org.id,
        role=OrganizationRole.OWNER,
    )
    response = auth_client.post(
        f"/api/organizations/{org.id}/members",
        json={"user_id": str(target.id), "role": "owner"},
        headers=_auth_header(owner),
    )
    assert response.status_code == 409
    assert response.json()["code"] == "owner_role_not_allowed"


# --- Slug ---


def test_slug_collision_club_club_2_club_3(auth_client, db_session) -> None:
    user = _create_user(db_session)
    headers = _auth_header(user)
    slugs = []
    for _ in range(3):
        response = auth_client.post(
            "/api/organizations",
            json=_org_payload("Club"),
            headers=headers,
        )
        assert response.status_code == 201
        slugs.append(response.json()["slug"])
    assert slugs == ["club", "club-2", "club-3"]


def test_slug_special_chars_normalized_via_api(auth_client, db_session) -> None:
    user = _create_user(db_session)
    response = auth_client.post(
        "/api/organizations",
        json=_org_payload("Café Événement"),
        headers=_auth_header(user),
    )
    assert response.status_code == 201
    assert response.json()["slug"] == slugify_name("Café Événement")


def test_slug_stable_after_name_patch(auth_client, db_session) -> None:
    user = _create_user(db_session)
    create = auth_client.post(
        "/api/organizations",
        json=_org_payload("Original Name"),
        headers=_auth_header(user),
    )
    org_id = create.json()["id"]
    original_slug = create.json()["slug"]
    update = auth_client.patch(
        f"/api/organizations/{org_id}",
        json={"name": "Completely Different"},
        headers=_auth_header(user),
    )
    assert update.status_code == 200
    assert update.json()["slug"] == original_slug


# --- Archive ---


def test_archive_logical_not_physical_delete(auth_client, db_session) -> None:
    owner = _create_user(db_session)
    create = auth_client.post(
        "/api/organizations",
        json=_org_payload("Archive Logical"),
        headers=_auth_header(owner),
    )
    org_id = create.json()["id"]
    auth_client.delete(
        f"/api/organizations/{org_id}",
        headers=_auth_header(owner),
    )
    org = db_session.get(Organization, org_id)
    assert org is not None
    assert org.status == OrganizationStatus.ARCHIVED


def test_archive_preserves_member_rows(auth_client, db_session) -> None:
    owner, admin, staff, _viewer, org, _ = _setup_org_with_roles(db_session)
    before = db_session.scalar(select(func.count()).select_from(OrganizationMember))
    auth_client.delete(
        f"/api/organizations/{org.id}",
        headers=_auth_header(owner),
    )
    after = db_session.scalar(select(func.count()).select_from(OrganizationMember))
    assert before == after
    assert after >= 4


def test_archived_excluded_from_member_list(auth_client, db_session) -> None:
    owner = _create_user(db_session)
    create = auth_client.post(
        "/api/organizations",
        json=_org_payload("List Exclude"),
        headers=_auth_header(owner),
    )
    org_id = create.json()["id"]
    auth_client.delete(
        f"/api/organizations/{org_id}",
        headers=_auth_header(owner),
    )
    response = auth_client.get("/api/organizations", headers=_auth_header(owner))
    assert all(item["id"] != org_id for item in response.json())


# --- Audit smoke ---


def test_all_org_audit_actions_on_happy_path(auth_client, db_session) -> None:
    owner = _create_user(db_session)
    staff = _create_user(db_session)
    create = auth_client.post(
        "/api/organizations",
        json=_org_payload("Audit Happy"),
        headers=_auth_header(owner),
    )
    org_id = create.json()["id"]
    auth_client.patch(
        f"/api/organizations/{org_id}",
        json={"description": "x"},
        headers=_auth_header(owner),
    )
    add = auth_client.post(
        f"/api/organizations/{org_id}/members",
        json={"user_id": str(staff.id), "role": "staff"},
        headers=_auth_header(owner),
    )
    member_id = add.json()["id"]
    auth_client.patch(
        f"/api/organizations/{org_id}/members/{member_id}",
        json={"role": "viewer"},
        headers=_auth_header(owner),
    )
    auth_client.delete(
        f"/api/organizations/{org_id}/members/{member_id}",
        headers=_auth_header(owner),
    )
    auth_client.delete(
        f"/api/organizations/{org_id}",
        headers=_auth_header(owner),
    )

    actions = {
        log.action
        for log in db_session.scalars(select(AuditLog).where(AuditLog.actor_user_id == owner.id))
    }
    expected = {
        AuditAction.ORGANIZATION_CREATED.value,
        AuditAction.ORGANIZATION_UPDATED.value,
        AuditAction.ORGANIZATION_ARCHIVED.value,
        AuditAction.ORGANIZATION_MEMBER_ADDED.value,
        AuditAction.ORGANIZATION_MEMBER_ROLE_UPDATED.value,
        AuditAction.ORGANIZATION_MEMBER_REMOVED.value,
    }
    assert expected.issubset(actions)


def test_member_audit_always_has_organization_id(auth_client, db_session) -> None:
    owner = _create_user(db_session)
    target = _create_user(db_session)
    org = OrganizationRepository(db_session).create(
        name="Audit Org Id",
        slug=f"audit-org-id-{uuid4().hex[:8]}",
        org_type=OrganizationType.NIGHTCLUB,
        created_by_user_id=owner.id,
        status=OrganizationStatus.ACTIVE,
    )
    OrganizationMemberRepository(db_session).add_member(
        user_id=owner.id,
        organization_id=org.id,
        role=OrganizationRole.OWNER,
    )
    auth_client.post(
        f"/api/organizations/{org.id}/members",
        json={"user_id": str(target.id), "role": "staff"},
        headers=_auth_header(owner),
    )
    logs = db_session.scalars(
        select(AuditLog).where(
            AuditLog.resource_type == "organization_member",
            AuditLog.action == AuditAction.ORGANIZATION_MEMBER_ADDED.value,
        )
    ).all()
    assert logs
    for log in logs:
        assert log.audit_metadata is not None
        assert log.audit_metadata.get("organization_id") == str(org.id)
