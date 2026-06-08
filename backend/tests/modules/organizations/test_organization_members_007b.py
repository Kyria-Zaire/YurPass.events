"""Organization members activation tests — TICKET-007B."""

from uuid import uuid4

import pytest
from app.modules.auth.constants import UserStatus
from app.modules.auth.models import User
from app.modules.auth.password import hash_password
from app.modules.organizations.constants import (
    MemberStatus,
    OrganizationRole,
    OrganizationStatus,
    OrganizationType,
)
from app.modules.organizations.models import Organization
from app.modules.organizations.repository import (
    OrganizationMemberRepository,
    OrganizationRepository,
)
from app.modules.organizations.schemas import OrganizationMemberPublic
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError


def test_organization_role_enum_values() -> None:
    assert OrganizationRole.OWNER.value == "owner"
    assert OrganizationRole.VIEWER.value == "viewer"
    assert len(OrganizationRole) == 4


def test_member_status_enum_values() -> None:
    assert MemberStatus.ACTIVE.value == "active"
    assert MemberStatus.LEFT.value == "left"
    assert len(MemberStatus) == 3


def test_migration_organization_members_activated(db_engine) -> None:
    inspector = inspect(db_engine)
    assert inspector.has_table("organization_members")

    columns = {column["name"] for column in inspector.get_columns("organization_members")}
    assert {"status", "updated_at", "role", "organization_id", "user_id"}.issubset(columns)

    indexes = {index["name"] for index in inspector.get_indexes("organization_members")}
    assert "ix_org_members_org_role" in indexes
    assert "uq_organization_members_user_org" in indexes

    foreign_keys = inspector.get_foreign_keys("organization_members")
    fk_targets = {(fk["referred_table"], tuple(fk["referred_columns"])) for fk in foreign_keys}
    assert ("organizations", ("id",)) in fk_targets


def test_postgres_member_enums_exist(db_engine) -> None:
    with db_engine.connect() as connection:
        result = connection.execute(
            text(
                "SELECT typname FROM pg_type "
                "WHERE typname IN ('organization_role', 'member_status')"
            )
        )
        enum_names = {row[0] for row in result}
    assert enum_names == {"organization_role", "member_status"}


def _create_user(db_session) -> User:
    user = User(
        email=f"member-{uuid4()}@example.com",
        password_hash=hash_password("SecurePass123!"),
        status=UserStatus.ACTIVE,
    )
    db_session.add(user)
    db_session.flush()
    return user


def _create_organization(db_session, user: User) -> Organization:
    return OrganizationRepository(db_session).create(
        name="Member Test Org",
        slug=f"member-org-{uuid4().hex[:8]}",
        org_type=OrganizationType.NIGHTCLUB,
        created_by_user_id=user.id,
        status=OrganizationStatus.ACTIVE,
    )


def test_unique_user_organization_pair(db_session) -> None:
    owner = _create_user(db_session)
    organization = _create_organization(db_session, owner)
    repository = OrganizationMemberRepository(db_session)

    repository.add_member(
        user_id=owner.id,
        organization_id=organization.id,
        role=OrganizationRole.OWNER,
    )

    with pytest.raises(IntegrityError):
        repository.add_member(
            user_id=owner.id,
            organization_id=organization.id,
            role=OrganizationRole.ADMIN,
        )


def test_fk_organization_id_enforced(db_session) -> None:
    user = _create_user(db_session)
    repository = OrganizationMemberRepository(db_session)

    with pytest.raises(IntegrityError):
        repository.add_member(
            user_id=user.id,
            organization_id=uuid4(),
            role=OrganizationRole.STAFF,
        )


def test_repository_add_get_list(db_session) -> None:
    owner = _create_user(db_session)
    staff = _create_user(db_session)
    organization = _create_organization(db_session, owner)
    repository = OrganizationMemberRepository(db_session)

    owner_member = repository.add_member(
        user_id=owner.id,
        organization_id=organization.id,
        role=OrganizationRole.OWNER,
    )
    staff_member = repository.add_member(
        user_id=staff.id,
        organization_id=organization.id,
        role=OrganizationRole.STAFF,
    )

    fetched = repository.get_member(owner.id, organization.id)
    assert fetched is not None
    assert fetched.id == owner_member.id

    by_id = repository.get_member_by_id(staff_member.id)
    assert by_id is not None
    assert by_id.role == OrganizationRole.STAFF

    members = repository.list_members(organization.id)
    assert len(members) == 2


def test_update_member_role_and_status(db_session) -> None:
    owner = _create_user(db_session)
    member_user = _create_user(db_session)
    organization = _create_organization(db_session, owner)
    repository = OrganizationMemberRepository(db_session)

    member = repository.add_member(
        user_id=member_user.id,
        organization_id=organization.id,
        role=OrganizationRole.VIEWER,
    )
    repository.update_member_role(member, OrganizationRole.ADMIN)
    repository.update_member_status(member, MemberStatus.SUSPENDED)

    refreshed = repository.get_member_by_id(member.id)
    assert refreshed is not None
    assert refreshed.role == OrganizationRole.ADMIN
    assert refreshed.status == MemberStatus.SUSPENDED


def test_count_active_owners(db_session) -> None:
    owner = _create_user(db_session)
    co_owner = _create_user(db_session)
    suspended_owner = _create_user(db_session)
    organization = _create_organization(db_session, owner)
    repository = OrganizationMemberRepository(db_session)

    repository.add_member(
        user_id=owner.id,
        organization_id=organization.id,
        role=OrganizationRole.OWNER,
    )
    repository.add_member(
        user_id=co_owner.id,
        organization_id=organization.id,
        role=OrganizationRole.OWNER,
    )
    suspended = repository.add_member(
        user_id=suspended_owner.id,
        organization_id=organization.id,
        role=OrganizationRole.OWNER,
    )
    repository.update_member_status(suspended, MemberStatus.SUSPENDED)

    assert repository.count_active_owners(organization.id) == 2


def test_organization_model_still_works(db_session) -> None:
    user = _create_user(db_session)
    organization = _create_organization(db_session, user)
    assert organization.id is not None
    assert organization.type == OrganizationType.NIGHTCLUB


def test_organization_member_public_schema(db_session) -> None:
    owner = _create_user(db_session)
    organization = _create_organization(db_session, owner)
    member = OrganizationMemberRepository(db_session).add_member(
        user_id=owner.id,
        organization_id=organization.id,
        role=OrganizationRole.OWNER,
    )
    public = OrganizationMemberPublic.model_validate(member)
    assert public.role == OrganizationRole.OWNER
    assert public.status == MemberStatus.ACTIVE


def test_organization_members_endpoints_defined_in_007e() -> None:
    from app.main import app

    member_paths = [
        route.path
        for route in app.routes
        if "/api/organizations" in getattr(route, "path", "")
        and "/members" in getattr(route, "path", "")
    ]
    assert len(member_paths) == 4
