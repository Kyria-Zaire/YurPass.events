"""Organizations foundation tests — TICKET-007A."""

from uuid import uuid4

import pytest
from app.modules.auth.constants import UserStatus
from app.modules.auth.models import User
from app.modules.auth.password import hash_password
from app.modules.organizations.constants import OrganizationStatus, OrganizationType
from app.modules.organizations.models import Organization, OrganizationMember
from app.modules.organizations.repository import OrganizationRepository
from app.modules.organizations.schemas import OrganizationPublic
from app.modules.organizations.slug import slugify_name
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError


def test_organization_type_enum_values() -> None:
    assert OrganizationType.NIGHTCLUB.value == "nightclub"
    assert OrganizationType.OTHER.value == "other"
    assert len(OrganizationType) == 8


def test_organization_status_enum_values() -> None:
    assert OrganizationStatus.DRAFT.value == "draft"
    assert OrganizationStatus.ARCHIVED.value == "archived"
    assert len(OrganizationStatus) == 4


def test_slugify_basic() -> None:
    assert slugify_name("  Club XYZ  ") == "club-xyz"
    assert slugify_name("Le Café Noir") == "le-cafe-noir"
    assert slugify_name("Festival été 2026!") == "festival-ete-2026"


def test_organization_model_has_expected_columns() -> None:
    columns = {column.name for column in Organization.__table__.columns}
    assert columns == {
        "id",
        "name",
        "slug",
        "type",
        "status",
        "description",
        "logo_url",
        "website_url",
        "city",
        "country",
        "created_by_user_id",
        "created_at",
        "updated_at",
    }


def test_organization_member_placeholder_unchanged(db_session) -> None:
    user = User(
        email=f"member-{uuid4()}@example.com",
        password_hash=hash_password("SecurePass123!"),
        status=UserStatus.ACTIVE,
    )
    db_session.add(user)
    db_session.flush()

    member = OrganizationMember(
        user_id=user.id,
        organization_id=uuid4(),
        role="owner",
    )
    db_session.add(member)
    db_session.flush()

    assert member.id is not None
    assert member.role == "owner"


def test_migration_creates_organizations_table(db_engine) -> None:
    inspector = inspect(db_engine)
    assert inspector.has_table("organizations")
    column_names = {column["name"] for column in inspector.get_columns("organizations")}
    assert "slug" in column_names
    assert "type" in column_names
    assert "status" in column_names


def test_postgres_enums_exist(db_engine) -> None:
    with db_engine.connect() as connection:
        result = connection.execute(
            text(
                "SELECT typname FROM pg_type "
                "WHERE typname IN ('organization_type', 'organization_status')"
            )
        )
        enum_names = {row[0] for row in result}
    assert enum_names == {"organization_type", "organization_status"}


def _create_user(db_session) -> User:
    user = User(
        email=f"org-owner-{uuid4()}@example.com",
        password_hash=hash_password("SecurePass123!"),
        status=UserStatus.ACTIVE,
    )
    db_session.add(user)
    db_session.flush()
    return user


def test_repository_create_and_get_by_slug(db_session) -> None:
    user = _create_user(db_session)
    repository = OrganizationRepository(db_session)
    slug = f"club-{uuid4().hex[:8]}"

    organization = repository.create(
        name="Club Test",
        slug=slug,
        org_type=OrganizationType.NIGHTCLUB,
        created_by_user_id=user.id,
        city="Paris",
        country="FR",
    )

    assert organization.id is not None
    assert organization.status == OrganizationStatus.DRAFT

    by_slug = repository.get_by_slug(slug)
    assert by_slug is not None
    assert by_slug.id == organization.id

    by_id = repository.get_by_id(organization.id)
    assert by_id is not None
    assert by_id.name == "Club Test"


def test_repository_slug_exists(db_session) -> None:
    user = _create_user(db_session)
    repository = OrganizationRepository(db_session)
    slug = f"exists-{uuid4().hex[:8]}"

    assert repository.slug_exists(slug) is False
    repository.create(
        name="Existing Club",
        slug=slug,
        org_type=OrganizationType.NIGHTCLUB,
        created_by_user_id=user.id,
    )
    assert repository.slug_exists(slug) is True


def test_repository_enforces_unique_slug(db_session) -> None:
    user = _create_user(db_session)
    repository = OrganizationRepository(db_session)
    slug = f"unique-{uuid4().hex[:8]}"

    repository.create(
        name="First",
        slug=slug,
        org_type=OrganizationType.NIGHTCLUB,
        created_by_user_id=user.id,
    )

    with pytest.raises(IntegrityError):
        repository.create(
            name="Second",
            slug=slug,
            org_type=OrganizationType.FESTIVAL,
            created_by_user_id=user.id,
        )


def test_organization_public_schema_from_model(db_session) -> None:
    user = _create_user(db_session)
    repository = OrganizationRepository(db_session)
    organization = repository.create(
        name="Schema Club",
        slug=f"schema-{uuid4().hex[:8]}",
        org_type=OrganizationType.VENUE,
        created_by_user_id=user.id,
    )

    public = OrganizationPublic.model_validate(organization)
    assert public.name == "Schema Club"
    assert public.type == OrganizationType.VENUE
    assert public.status == OrganizationStatus.DRAFT
