"""Events business logic — TICKET-008B."""

import uuid

from app.modules.auth.models import User
from app.modules.events.repository import EventRepository
from app.modules.events.schemas import EventCreate, EventPublic, EventUpdate
from app.modules.events.slug import resolve_unique_slug, slugify_name
from app.modules.organizations.repository import OrganizationRepository
from app.shared.exceptions import NotFoundError, ValidationError


class EventService:
    """Service layer for Events module."""

    def __init__(
        self,
        event_repository: EventRepository,
        organization_repository: OrganizationRepository,
    ) -> None:
        self._events = event_repository
        self._organizations = organization_repository

    def create(
        self,
        organization_id: uuid.UUID,
        user: User,
        payload: EventCreate,
    ) -> EventPublic:
        """Create a draft event with a unique slug."""
        self._ensure_organization_exists(organization_id)
        self._validate_schedule(payload.starts_at, payload.ends_at)

        base_slug = slugify_name(payload.name)
        slug = resolve_unique_slug(base_slug, self._events.slug_exists)
        event = self._events.create(
            name=payload.name,
            slug=slug,
            organization_id=organization_id,
            event_type=payload.event_type,
            created_by_user_id=user.id,
            starts_at=payload.starts_at,
            ends_at=payload.ends_at,
            visibility=payload.visibility,
            description=payload.description,
            cover_image_url=payload.cover_image_url,
            venue_name=payload.venue_name,
            city=payload.city,
            country=payload.country,
        )
        return EventPublic.model_validate(event)

    def list_for_organization(self, organization_id: uuid.UUID) -> list[EventPublic]:
        """List non-archived events for an organization."""
        self._ensure_organization_exists(organization_id)
        events = self._events.list_by_organization(organization_id)
        return [EventPublic.model_validate(event) for event in events]

    def get(self, organization_id: uuid.UUID, event_id: uuid.UUID) -> EventPublic:
        """Return event detail scoped to an organization."""
        event = self._get_event_or_404(event_id, organization_id)
        return EventPublic.model_validate(event)

    def update(
        self,
        organization_id: uuid.UUID,
        event_id: uuid.UUID,
        payload: EventUpdate,
    ) -> EventPublic:
        """Update event fields — slug remains stable."""
        event = self._get_event_or_404(event_id, organization_id)
        data = payload.model_dump(exclude_unset=True)
        starts_at = data.get("starts_at", event.starts_at)
        ends_at = data.get("ends_at", event.ends_at)
        self._validate_schedule(starts_at, ends_at)

        event = self._events.update(
            event,
            name=data.get("name"),
            description=data.get("description"),
            event_type=data.get("event_type"),
            visibility=data.get("visibility"),
            starts_at=data.get("starts_at"),
            ends_at=data.get("ends_at"),
            cover_image_url=data.get("cover_image_url"),
            venue_name=data.get("venue_name"),
            city=data.get("city"),
            country=data.get("country"),
        )
        return EventPublic.model_validate(event)

    def archive(self, organization_id: uuid.UUID, event_id: uuid.UUID) -> EventPublic:
        """Archive an event logically."""
        event = self._get_event_or_404(event_id, organization_id)
        event = self._events.archive(event)
        return EventPublic.model_validate(event)

    def _ensure_organization_exists(self, organization_id: uuid.UUID) -> None:
        if self._organizations.get_by_id(organization_id) is None:
            raise NotFoundError("Organization not found")

    def _get_event_or_404(self, event_id: uuid.UUID, organization_id: uuid.UUID):
        event = self._events.get_by_id_and_org(event_id, organization_id)
        if event is None:
            raise NotFoundError("Event not found")
        return event

    @staticmethod
    def _validate_schedule(starts_at, ends_at) -> None:
        if ends_at <= starts_at:
            raise ValidationError("ends_at must be after starts_at")
