"""Organizations CRUD tests — TICKET-007D."""

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
from sqlalchemy import select


def _create_user(
    db_session,
    *,
    global_role: GlobalRole = GlobalRole.USER,
) -> User:
    user = User(
        email=f"crud-{uuid4()}@example.com",
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


def _create_payload(name: str = "Club XYZ") -> dict:
    return {
        "name": name,
        "type": "nightclub",
        "description": "Test club",
        "city": "Paris",
        "country": "FR",
    }


def test_create_organization_success(auth_client, db_session) -> None:
    user = _create_user(db_session)
    response = auth_client.post(
        "/api/organizations",
        json=_create_payload(),
        headers=_auth_header(user),
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["name"] == "Club XYZ"
    assert payload["status"] == "draft"
    assert payload["slug"] == "club-xyz"
    assert payload["created_by_user_id"] == str(user.id)


def test_create_organization_adds_active_owner(auth_client, db_session) -> None:
    user = _create_user(db_session)
    response = auth_client.post(
        "/api/organizations",
        json=_create_payload("Owner Club"),
        headers=_auth_header(user),
    )
    org_id = response.json()["id"]
    member = OrganizationMemberRepository(db_session).get_member(user.id, org_id)
    assert member is not None
    assert member.role == OrganizationRole.OWNER
    assert member.status == MemberStatus.ACTIVE


def test_slug_collision_club_and_club_2(auth_client, db_session) -> None:
    user = _create_user(db_session)
    headers = _auth_header(user)

    first = auth_client.post(
        "/api/organizations",
        json=_create_payload("Club"),
        headers=headers,
    )
    second = auth_client.post(
        "/api/organizations",
        json=_create_payload("Club"),
        headers=headers,
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["slug"] == "club"
    assert second.json()["slug"] == "club-2"


def test_list_only_member_organizations(auth_client, db_session) -> None:
    user_a = _create_user(db_session)
    user_b = _create_user(db_session)
    org_repo = OrganizationRepository(db_session)
    member_repo = OrganizationMemberRepository(db_session)

    org_a = org_repo.create(
        name="Org A",
        slug=f"org-a-{uuid4().hex[:6]}",
        org_type=OrganizationType.NIGHTCLUB,
        created_by_user_id=user_a.id,
    )
    org_b = org_repo.create(
        name="Org B",
        slug=f"org-b-{uuid4().hex[:6]}",
        org_type=OrganizationType.NIGHTCLUB,
        created_by_user_id=user_b.id,
    )
    member_repo.add_member(user_id=user_a.id, organization_id=org_a.id, role=OrganizationRole.OWNER)
    member_repo.add_member(user_id=user_b.id, organization_id=org_b.id, role=OrganizationRole.OWNER)

    response = auth_client.get("/api/organizations", headers=_auth_header(user_a))
    assert response.status_code == 200
    ids = {item["id"] for item in response.json()}
    assert str(org_a.id) in ids
    assert str(org_b.id) not in ids


def test_super_admin_lists_all_non_archived(auth_client, db_session) -> None:
    owner = _create_user(db_session)
    super_admin = _create_user(db_session, global_role=GlobalRole.SUPER_ADMIN)
    org_repo = OrganizationRepository(db_session)
    member_repo = OrganizationMemberRepository(db_session)

    org_visible = org_repo.create(
        name="Visible",
        slug=f"visible-{uuid4().hex[:6]}",
        org_type=OrganizationType.NIGHTCLUB,
        created_by_user_id=owner.id,
    )
    org_archived = org_repo.create(
        name="Archived",
        slug=f"archived-{uuid4().hex[:6]}",
        org_type=OrganizationType.NIGHTCLUB,
        created_by_user_id=owner.id,
        status=OrganizationStatus.ARCHIVED,
    )
    member_repo.add_member(
        user_id=owner.id,
        organization_id=org_visible.id,
        role=OrganizationRole.OWNER,
    )
    member_repo.add_member(
        user_id=owner.id,
        organization_id=org_archived.id,
        role=OrganizationRole.OWNER,
    )

    response = auth_client.get("/api/organizations", headers=_auth_header(super_admin))
    assert response.status_code == 200
    ids = {item["id"] for item in response.json()}
    assert str(org_visible.id) in ids
    assert str(org_archived.id) not in ids


def test_detail_requires_active_member(auth_client, db_session) -> None:
    owner = _create_user(db_session)
    outsider = _create_user(db_session)
    create = auth_client.post(
        "/api/organizations",
        json=_create_payload("Detail Org"),
        headers=_auth_header(owner),
    )
    org_id = create.json()["id"]

    denied = auth_client.get(
        f"/api/organizations/{org_id}",
        headers=_auth_header(outsider),
    )
    assert denied.status_code == 403

    allowed = auth_client.get(
        f"/api/organizations/{org_id}",
        headers=_auth_header(owner),
    )
    assert allowed.status_code == 200


def test_update_owner_and_admin_allowed(auth_client, db_session) -> None:
    owner = _create_user(db_session)
    admin = _create_user(db_session)
    create = auth_client.post(
        "/api/organizations",
        json=_create_payload("Update Org"),
        headers=_auth_header(owner),
    )
    org_id = create.json()["id"]
    OrganizationMemberRepository(db_session).add_member(
        user_id=admin.id,
        organization_id=org_id,
        role=OrganizationRole.ADMIN,
    )

    owner_update = auth_client.patch(
        f"/api/organizations/{org_id}",
        json={"description": "Owner edit"},
        headers=_auth_header(owner),
    )
    admin_update = auth_client.patch(
        f"/api/organizations/{org_id}",
        json={"city": "Lyon"},
        headers=_auth_header(admin),
    )

    assert owner_update.status_code == 200
    assert admin_update.status_code == 200
    assert owner_update.json()["description"] == "Owner edit"
    assert admin_update.json()["city"] == "Lyon"


def test_update_staff_and_viewer_refused(auth_client, db_session) -> None:
    owner = _create_user(db_session)
    staff = _create_user(db_session)
    viewer = _create_user(db_session)
    create = auth_client.post(
        "/api/organizations",
        json=_create_payload("RBAC Update"),
        headers=_auth_header(owner),
    )
    org_id = create.json()["id"]
    member_repo = OrganizationMemberRepository(db_session)
    member_repo.add_member(user_id=staff.id, organization_id=org_id, role=OrganizationRole.STAFF)
    member_repo.add_member(user_id=viewer.id, organization_id=org_id, role=OrganizationRole.VIEWER)

    staff_resp = auth_client.patch(
        f"/api/organizations/{org_id}",
        json={"description": "Nope"},
        headers=_auth_header(staff),
    )
    viewer_resp = auth_client.patch(
        f"/api/organizations/{org_id}",
        json={"description": "Nope"},
        headers=_auth_header(viewer),
    )

    assert staff_resp.status_code == 403
    assert viewer_resp.status_code == 403


def test_slug_stable_when_name_changes(auth_client, db_session) -> None:
    user = _create_user(db_session)
    create = auth_client.post(
        "/api/organizations",
        json=_create_payload("Stable Slug Club"),
        headers=_auth_header(user),
    )
    org_id = create.json()["id"]
    original_slug = create.json()["slug"]

    update = auth_client.patch(
        f"/api/organizations/{org_id}",
        json={"name": "Renamed Club Name"},
        headers=_auth_header(user),
    )

    assert update.status_code == 200
    assert update.json()["name"] == "Renamed Club Name"
    assert update.json()["slug"] == original_slug


def test_archive_owner_allowed(auth_client, db_session) -> None:
    user = _create_user(db_session)
    create = auth_client.post(
        "/api/organizations",
        json=_create_payload("Archive Me"),
        headers=_auth_header(user),
    )
    org_id = create.json()["id"]

    response = auth_client.delete(
        f"/api/organizations/{org_id}",
        headers=_auth_header(user),
    )
    assert response.status_code == 200
    assert response.json()["status"] == "archived"


def test_archive_admin_staff_viewer_refused(auth_client, db_session) -> None:
    owner = _create_user(db_session)
    admin = _create_user(db_session)
    staff = _create_user(db_session)
    viewer = _create_user(db_session)
    create = auth_client.post(
        "/api/organizations",
        json=_create_payload("Archive RBAC"),
        headers=_auth_header(owner),
    )
    org_id = create.json()["id"]
    member_repo = OrganizationMemberRepository(db_session)
    member_repo.add_member(user_id=admin.id, organization_id=org_id, role=OrganizationRole.ADMIN)
    member_repo.add_member(user_id=staff.id, organization_id=org_id, role=OrganizationRole.STAFF)
    member_repo.add_member(user_id=viewer.id, organization_id=org_id, role=OrganizationRole.VIEWER)

    archive_url = f"/api/organizations/{org_id}"
    assert auth_client.delete(archive_url, headers=_auth_header(admin)).status_code == 403
    assert auth_client.delete(archive_url, headers=_auth_header(staff)).status_code == 403
    assert auth_client.delete(archive_url, headers=_auth_header(viewer)).status_code == 403


def test_archived_organization_excluded_from_list(auth_client, db_session) -> None:
    user = _create_user(db_session)
    create = auth_client.post(
        "/api/organizations",
        json=_create_payload("List Archive"),
        headers=_auth_header(user),
    )
    org_id = create.json()["id"]
    auth_client.delete(f"/api/organizations/{org_id}", headers=_auth_header(user))

    response = auth_client.get("/api/organizations", headers=_auth_header(user))
    assert response.status_code == 200
    assert all(item["id"] != org_id for item in response.json())


def test_audit_created_updated_archived(auth_client, db_session) -> None:
    user = _create_user(db_session)
    create = auth_client.post(
        "/api/organizations",
        json=_create_payload("Audit Org"),
        headers=_auth_header(user),
    )
    org_id = create.json()["id"]

    auth_client.patch(
        f"/api/organizations/{org_id}",
        json={"description": "Audited"},
        headers=_auth_header(user),
    )
    auth_client.delete(f"/api/organizations/{org_id}", headers=_auth_header(user))

    actions = {
        log.action
        for log in db_session.scalars(
            select(AuditLog).where(AuditLog.resource_id == org_id)
        )
    }
    assert AuditAction.ORGANIZATION_CREATED.value in actions
    assert AuditAction.ORGANIZATION_UPDATED.value in actions
    assert AuditAction.ORGANIZATION_ARCHIVED.value in actions


def test_members_endpoints_defined_in_007e() -> None:
    from app.main import app

    member_paths = [
        route.path
        for route in app.routes
        if "/api/organizations" in getattr(route, "path", "")
        and "/members" in getattr(route, "path", "")
    ]
    assert len(member_paths) == 4
