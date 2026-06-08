"""Event CRUD tests — TICKET-008B."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.core.config import get_settings
from app.modules.auth.constants import GlobalRole, UserStatus
from app.modules.auth.models import User
from app.modules.auth.password import hash_password
from app.modules.auth.tokens import create_access_token
from app.modules.events.constants import EventStatus, EventType, EventVisibility
from app.modules.events.repository import EventRepository
from app.modules.organizations.constants import MemberStatus, OrganizationRole, OrganizationType
from app.modules.organizations.repository import (
    OrganizationMemberRepository,
    OrganizationRepository,
)


def _create_user(
    db_session,
    *,
    global_role: GlobalRole = GlobalRole.USER,
) -> User:
    user = User(
        email=f"evt-{uuid4()}@example.com",
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
        name=f"Org {uuid4().hex[:6]}",
        slug=f"org-{uuid4().hex[:8]}",
        org_type=OrganizationType.NIGHTCLUB,
        created_by_user_id=owner.id,
    )
    member_repo.add_member(
        user_id=owner.id,
        organization_id=org.id,
        role=OrganizationRole.OWNER,
    )
    return org


def _add_member(db_session, org, user: User, role: OrganizationRole) -> None:
    OrganizationMemberRepository(db_session).add_member(
        user_id=user.id,
        organization_id=org.id,
        role=role,
    )


def _events_base(org_id) -> str:
    return f"/api/organizations/{org_id}/events"


def _event_payload(name: str = "Summer Party") -> dict:
    starts = datetime.now(UTC) + timedelta(days=7)
    ends = starts + timedelta(hours=5)
    return {
        "name": name,
        "description": "Big night",
        "event_type": "nightclub",
        "visibility": "private",
        "starts_at": starts.isoformat(),
        "ends_at": ends.isoformat(),
        "venue_name": "Main Hall",
        "city": "Paris",
        "country": "FR",
    }


def test_events_endpoints_defined(auth_client) -> None:
    routes = {route.path for route in auth_client.app.routes}
    assert "/api/organizations/{organization_id}/events" in routes
    assert "/api/organizations/{organization_id}/events/{event_id}" in routes
    assert "/api/events" not in routes


def test_create_event_success(auth_client, db_session) -> None:
    owner = _create_user(db_session)
    org = _create_org_with_owner(db_session, owner)
    response = auth_client.post(
        _events_base(org.id),
        json=_event_payload("Summer Party"),
        headers=_auth_header(owner),
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["name"] == "Summer Party"
    assert payload["status"] == "draft"
    assert payload["slug"] == "summer-party"
    assert payload["organization_id"] == str(org.id)
    assert payload["created_by_user_id"] == str(owner.id)


def test_create_event_slug_collision(auth_client, db_session) -> None:
    owner = _create_user(db_session)
    org = _create_org_with_owner(db_session, owner)
    headers = _auth_header(owner)

    first = auth_client.post(
        _events_base(org.id),
        json=_event_payload("Gala"),
        headers=headers,
    )
    second = auth_client.post(
        _events_base(org.id),
        json=_event_payload("Gala"),
        headers=headers,
    )
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["slug"] == "gala"
    assert second.json()["slug"] == "gala-2"


def test_list_events_excludes_archived(auth_client, db_session) -> None:
    owner = _create_user(db_session)
    org = _create_org_with_owner(db_session, owner)
    event_repo = EventRepository(db_session)
    starts = datetime.now(UTC) + timedelta(days=1)
    ends = starts + timedelta(hours=3)

    active = event_repo.create(
        organization_id=org.id,
        created_by_user_id=owner.id,
        name="Active Event",
        slug=f"active-{uuid4().hex[:6]}",
        event_type=EventType.NIGHTCLUB,
        visibility=EventVisibility.PRIVATE,
        starts_at=starts,
        ends_at=ends,
    )
    event_repo.create(
        organization_id=org.id,
        created_by_user_id=owner.id,
        name="Archived Event",
        slug=f"archived-{uuid4().hex[:6]}",
        event_type=EventType.NIGHTCLUB,
        visibility=EventVisibility.PRIVATE,
        starts_at=starts,
        ends_at=ends,
        status=EventStatus.ARCHIVED,
    )

    response = auth_client.get(_events_base(org.id), headers=_auth_header(owner))
    assert response.status_code == 200
    ids = {item["id"] for item in response.json()}
    assert str(active.id) in ids
    assert len(ids) == 1


def test_get_event_detail(auth_client, db_session) -> None:
    owner = _create_user(db_session)
    org = _create_org_with_owner(db_session, owner)
    create = auth_client.post(
        _events_base(org.id),
        json=_event_payload("Detail Night"),
        headers=_auth_header(owner),
    )
    event_id = create.json()["id"]

    response = auth_client.get(
        f"{_events_base(org.id)}/{event_id}",
        headers=_auth_header(owner),
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Detail Night"


def test_update_event_slug_stable(auth_client, db_session) -> None:
    owner = _create_user(db_session)
    org = _create_org_with_owner(db_session, owner)
    create = auth_client.post(
        _events_base(org.id),
        json=_event_payload("Original Name"),
        headers=_auth_header(owner),
    )
    event_id = create.json()["id"]
    original_slug = create.json()["slug"]

    response = auth_client.patch(
        f"{_events_base(org.id)}/{event_id}",
        json={"name": "Renamed Event"},
        headers=_auth_header(owner),
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Renamed Event"
    assert response.json()["slug"] == original_slug


def test_delete_event_archives(auth_client, db_session) -> None:
    owner = _create_user(db_session)
    org = _create_org_with_owner(db_session, owner)
    create = auth_client.post(
        _events_base(org.id),
        json=_event_payload("To Archive"),
        headers=_auth_header(owner),
    )
    event_id = create.json()["id"]

    delete = auth_client.delete(
        f"{_events_base(org.id)}/{event_id}",
        headers=_auth_header(owner),
    )
    assert delete.status_code == 200
    assert delete.json()["status"] == "archived"

    get_resp = auth_client.get(
        f"{_events_base(org.id)}/{event_id}",
        headers=_auth_header(owner),
    )
    assert get_resp.status_code == 200
    assert get_resp.json()["status"] == "archived"


def test_create_rejects_invalid_schedule(auth_client, db_session) -> None:
    owner = _create_user(db_session)
    org = _create_org_with_owner(db_session, owner)
    starts = datetime.now(UTC) + timedelta(days=2)
    ends = starts - timedelta(hours=1)
    response = auth_client.post(
        _events_base(org.id),
        json={
            **_event_payload(),
            "starts_at": starts.isoformat(),
            "ends_at": ends.isoformat(),
        },
        headers=_auth_header(owner),
    )
    assert response.status_code == 400


def test_staff_can_read_events(auth_client, db_session) -> None:
    owner = _create_user(db_session)
    staff = _create_user(db_session)
    org = _create_org_with_owner(db_session, owner)
    _add_member(db_session, org, staff, OrganizationRole.STAFF)

    create = auth_client.post(
        _events_base(org.id),
        json=_event_payload("Staff Read"),
        headers=_auth_header(owner),
    )
    event_id = create.json()["id"]

    list_resp = auth_client.get(_events_base(org.id), headers=_auth_header(staff))
    detail_resp = auth_client.get(
        f"{_events_base(org.id)}/{event_id}",
        headers=_auth_header(staff),
    )
    assert list_resp.status_code == 200
    assert detail_resp.status_code == 200


def test_staff_cannot_create_event(auth_client, db_session) -> None:
    owner = _create_user(db_session)
    staff = _create_user(db_session)
    org = _create_org_with_owner(db_session, owner)
    _add_member(db_session, org, staff, OrganizationRole.STAFF)

    response = auth_client.post(
        _events_base(org.id),
        json=_event_payload(),
        headers=_auth_header(staff),
    )
    assert response.status_code == 403


def test_viewer_denied_events(auth_client, db_session) -> None:
    owner = _create_user(db_session)
    viewer = _create_user(db_session)
    org = _create_org_with_owner(db_session, owner)
    _add_member(db_session, org, viewer, OrganizationRole.VIEWER)

    auth_client.post(
        _events_base(org.id),
        json=_event_payload(),
        headers=_auth_header(owner),
    )

    list_resp = auth_client.get(_events_base(org.id), headers=_auth_header(viewer))
    assert list_resp.status_code == 403


def test_admin_can_update_and_archive(auth_client, db_session) -> None:
    owner = _create_user(db_session)
    admin = _create_user(db_session)
    org = _create_org_with_owner(db_session, owner)
    _add_member(db_session, org, admin, OrganizationRole.ADMIN)

    create = auth_client.post(
        _events_base(org.id),
        json=_event_payload("Admin Event"),
        headers=_auth_header(owner),
    )
    event_id = create.json()["id"]

    patch = auth_client.patch(
        f"{_events_base(org.id)}/{event_id}",
        json={"description": "Updated by admin"},
        headers=_auth_header(admin),
    )
    assert patch.status_code == 200

    delete = auth_client.delete(
        f"{_events_base(org.id)}/{event_id}",
        headers=_auth_header(admin),
    )
    assert delete.status_code == 200
    assert delete.json()["status"] == "archived"


def test_non_member_denied(auth_client, db_session) -> None:
    owner = _create_user(db_session)
    outsider = _create_user(db_session)
    org = _create_org_with_owner(db_session, owner)

    response = auth_client.get(_events_base(org.id), headers=_auth_header(outsider))
    assert response.status_code == 403


def test_super_admin_bypass_read(auth_client, db_session) -> None:
    owner = _create_user(db_session)
    super_admin = _create_user(db_session, global_role=GlobalRole.SUPER_ADMIN)
    org = _create_org_with_owner(db_session, owner)

    create = auth_client.post(
        _events_base(org.id),
        json=_event_payload("Super Read"),
        headers=_auth_header(owner),
    )
    event_id = create.json()["id"]

    list_resp = auth_client.get(_events_base(org.id), headers=_auth_header(super_admin))
    detail_resp = auth_client.get(
        f"{_events_base(org.id)}/{event_id}",
        headers=_auth_header(super_admin),
    )
    assert list_resp.status_code == 200
    assert detail_resp.status_code == 200


def test_inactive_member_denied(auth_client, db_session) -> None:
    owner = _create_user(db_session)
    inactive = _create_user(db_session)
    org = _create_org_with_owner(db_session, owner)
    member_repo = OrganizationMemberRepository(db_session)
    member_repo.add_member(
        user_id=inactive.id,
        organization_id=org.id,
        role=OrganizationRole.STAFF,
        status=MemberStatus.SUSPENDED,
    )

    response = auth_client.get(_events_base(org.id), headers=_auth_header(inactive))
    assert response.status_code == 403
