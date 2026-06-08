"""Events foundation tests — TICKET-008A."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from app.modules.auth.constants import UserStatus
from app.modules.auth.models import User
from app.modules.auth.password import hash_password
from app.modules.events.constants import EventStatus, EventType, EventVisibility
from app.modules.events.models import Event
from app.modules.events.repository import EventRepository
from app.modules.events.schemas import EventPublic
from app.modules.organizations.constants import OrganizationStatus, OrganizationType
from app.modules.organizations.repository import OrganizationRepository
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError


def test_event_type_enum_values() -> None:
    assert EventType.NIGHTCLUB.value == "nightclub"
    assert EventType.OTHER.value == "other"
    assert len(EventType) == 7


def test_event_status_enum_values() -> None:
    assert EventStatus.DRAFT.value == "draft"
    assert EventStatus.PUBLISHED.value == "published"
    assert EventStatus.ARCHIVED.value == "archived"
    assert len(EventStatus) == 5


def test_event_visibility_enum_values() -> None:
    assert EventVisibility.PUBLIC.value == "public"
    assert EventVisibility.PRIVATE.value == "private"
    assert len(EventVisibility) == 3


def test_event_model_has_expected_columns() -> None:
    columns = {column.name for column in Event.__table__.columns}
    assert columns == {
        "id",
        "organization_id",
        "name",
        "slug",
        "description",
        "event_type",
        "status",
        "visibility",
        "starts_at",
        "ends_at",
        "cover_image_url",
        "venue_name",
        "city",
        "country",
        "created_by_user_id",
        "created_at",
        "updated_at",
    }


def test_event_model_has_organization_and_user_relationships() -> None:
    assert "organization" in Event.__mapper__.relationships
    assert "created_by_user" in Event.__mapper__.relationships
    assert "tickets" not in Event.__mapper__.relationships


def test_migration_creates_events_table(db_engine) -> None:
    inspector = inspect(db_engine)
    assert inspector.has_table("events")
    column_names = {column["name"] for column in inspector.get_columns("events")}
    assert {
        "organization_id",
        "slug",
        "event_type",
        "status",
        "visibility",
        "starts_at",
    }.issubset(column_names)


def test_postgres_event_enums_exist(db_engine) -> None:
    with db_engine.connect() as connection:
        result = connection.execute(
            text(
                "SELECT typname FROM pg_type "
                "WHERE typname IN ('event_type', 'event_status', 'event_visibility')"
            )
        )
        enum_names = {row[0] for row in result}
    assert enum_names == {"event_type", "event_status", "event_visibility"}


def test_events_indexes_present(db_engine) -> None:
    inspector = inspect(db_engine)
    indexes = {index["name"] for index in inspector.get_indexes("events")}
    assert "ix_events_slug" in indexes
    assert "ix_events_organization_id" in indexes
    assert "ix_events_status" in indexes
    assert "ix_events_visibility" in indexes
    assert "ix_events_starts_at" in indexes
    slug_indexes = inspector.get_indexes("events")
    slug_index = next(idx for idx in slug_indexes if idx["name"] == "ix_events_slug")
    assert slug_index["unique"] is True


def _create_user(db_session) -> User:
    user = User(
        email=f"event-{uuid4()}@example.com",
        password_hash=hash_password("SecurePass123!"),
        status=UserStatus.ACTIVE,
    )
    db_session.add(user)
    db_session.flush()
    return user


def _create_organization(db_session, user: User):
    return OrganizationRepository(db_session).create(
        name="Event Org",
        slug=f"event-org-{uuid4().hex[:8]}",
        org_type=OrganizationType.NIGHTCLUB,
        created_by_user_id=user.id,
        status=OrganizationStatus.ACTIVE,
    )


def _event_times() -> tuple[datetime, datetime]:
    starts = datetime(2026, 9, 1, 20, 0, tzinfo=UTC)
    ends = starts + timedelta(hours=5)
    return starts, ends


def test_fk_organization_id_enforced(db_session) -> None:
    user = _create_user(db_session)
    starts_at, ends_at = _event_times()
    repository = EventRepository(db_session)

    with pytest.raises(IntegrityError):
        repository.create(
            name="Orphan Event",
            slug=f"orphan-{uuid4().hex[:8]}",
            organization_id=uuid4(),
            event_type=EventType.NIGHTCLUB,
            created_by_user_id=user.id,
            starts_at=starts_at,
            ends_at=ends_at,
        )


def test_fk_created_by_user_id_enforced(db_session) -> None:
    user = _create_user(db_session)
    organization = _create_organization(db_session, user)
    starts_at, ends_at = _event_times()
    repository = EventRepository(db_session)

    with pytest.raises(IntegrityError):
        repository.create(
            name="No User Event",
            slug=f"no-user-{uuid4().hex[:8]}",
            organization_id=organization.id,
            event_type=EventType.CONCERT,
            created_by_user_id=uuid4(),
            starts_at=starts_at,
            ends_at=ends_at,
        )


def test_repository_enforces_unique_slug(db_session) -> None:
    user = _create_user(db_session)
    organization = _create_organization(db_session, user)
    starts_at, ends_at = _event_times()
    repository = EventRepository(db_session)
    slug = f"unique-event-{uuid4().hex[:8]}"

    repository.create(
        name="First Event",
        slug=slug,
        organization_id=organization.id,
        event_type=EventType.FESTIVAL,
        created_by_user_id=user.id,
        starts_at=starts_at,
        ends_at=ends_at,
    )

    with pytest.raises(IntegrityError):
        repository.create(
            name="Second Event",
            slug=slug,
            organization_id=organization.id,
            event_type=EventType.CONCERT,
            created_by_user_id=user.id,
            starts_at=starts_at,
            ends_at=ends_at,
        )


def test_repository_create_get_by_slug_and_slug_exists(db_session) -> None:
    user = _create_user(db_session)
    organization = _create_organization(db_session, user)
    starts_at, ends_at = _event_times()
    repository = EventRepository(db_session)
    slug = f"repo-event-{uuid4().hex[:8]}"

    assert repository.slug_exists(slug) is False

    event = repository.create(
        name="Repo Event",
        slug=slug,
        organization_id=organization.id,
        event_type=EventType.NIGHTCLUB,
        created_by_user_id=user.id,
        starts_at=starts_at,
        ends_at=ends_at,
        city="Paris",
        country="FR",
    )

    assert event.id is not None
    assert event.status == EventStatus.DRAFT
    assert event.visibility == EventVisibility.PUBLIC

    by_slug = repository.get_by_slug(slug)
    assert by_slug is not None
    assert by_slug.id == event.id

    by_id = repository.get_by_id(event.id)
    assert by_id is not None
    assert by_id.name == "Repo Event"

    assert repository.slug_exists(slug) is True


def test_event_public_schema_from_model(db_session) -> None:
    user = _create_user(db_session)
    organization = _create_organization(db_session, user)
    starts_at, ends_at = _event_times()
    event = EventRepository(db_session).create(
        name="Schema Event",
        slug=f"schema-{uuid4().hex[:8]}",
        organization_id=organization.id,
        event_type=EventType.ASSOCIATION,
        created_by_user_id=user.id,
        starts_at=starts_at,
        ends_at=ends_at,
    )

    public = EventPublic.model_validate(event)
    assert public.name == "Schema Event"
    assert public.event_type == EventType.ASSOCIATION
    assert public.status == EventStatus.DRAFT
    assert public.organization_id == organization.id


def test_no_events_endpoints_exposed() -> None:
    from app.main import app

    event_paths = [
        route.path
        for route in app.routes
        if "/events" in getattr(route, "path", "")
    ]
    assert event_paths == []
