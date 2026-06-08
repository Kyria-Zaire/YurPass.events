"""Events data access."""

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.events.constants import EventStatus, EventType, EventVisibility
from app.modules.events.models import Event


class EventRepository:
    """Repository layer for Event persistence."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, event_id: uuid.UUID) -> Event | None:
        """Return an event by primary key."""
        return self._session.get(Event, event_id)

    def get_by_slug(self, slug: str) -> Event | None:
        """Return an event by unique slug."""
        statement = select(Event).where(Event.slug == slug)
        return self._session.scalar(statement)

    def slug_exists(self, slug: str) -> bool:
        """Return True when a slug is already taken."""
        return self.get_by_slug(slug) is not None

    def create(
        self,
        *,
        name: str,
        slug: str,
        organization_id: uuid.UUID,
        event_type: EventType,
        created_by_user_id: uuid.UUID,
        starts_at: datetime,
        ends_at: datetime,
        status: EventStatus = EventStatus.DRAFT,
        visibility: EventVisibility = EventVisibility.PUBLIC,
        description: str | None = None,
        cover_image_url: str | None = None,
        venue_name: str | None = None,
        city: str | None = None,
        country: str | None = None,
    ) -> Event:
        """Persist a new event."""
        event = Event(
            name=name,
            slug=slug,
            organization_id=organization_id,
            event_type=event_type,
            status=status,
            visibility=visibility,
            starts_at=starts_at,
            ends_at=ends_at,
            description=description,
            cover_image_url=cover_image_url,
            venue_name=venue_name,
            city=city,
            country=country,
            created_by_user_id=created_by_user_id,
        )
        self._session.add(event)
        self._session.flush()
        self._session.refresh(event)
        return event

    def get_by_id_and_org(
        self,
        event_id: uuid.UUID,
        organization_id: uuid.UUID,
    ) -> Event | None:
        """Return an event scoped to an organization."""
        statement = select(Event).where(
            Event.id == event_id,
            Event.organization_id == organization_id,
        )
        return self._session.scalar(statement)

    def list_by_organization(self, organization_id: uuid.UUID) -> list[Event]:
        """List non-archived events for an organization."""
        statement = (
            select(Event)
            .where(
                Event.organization_id == organization_id,
                Event.status != EventStatus.ARCHIVED,
            )
            .order_by(Event.starts_at)
        )
        return list(self._session.scalars(statement))

    def update(
        self,
        event: Event,
        *,
        name: str | None = None,
        description: str | None = None,
        event_type: EventType | None = None,
        visibility: EventVisibility | None = None,
        starts_at: datetime | None = None,
        ends_at: datetime | None = None,
        cover_image_url: str | None = None,
        venue_name: str | None = None,
        city: str | None = None,
        country: str | None = None,
    ) -> Event:
        """Apply partial field updates — slug is never modified here."""
        if name is not None:
            event.name = name
        if description is not None:
            event.description = description
        if event_type is not None:
            event.event_type = event_type
        if visibility is not None:
            event.visibility = visibility
        if starts_at is not None:
            event.starts_at = starts_at
        if ends_at is not None:
            event.ends_at = ends_at
        if cover_image_url is not None:
            event.cover_image_url = cover_image_url
        if venue_name is not None:
            event.venue_name = venue_name
        if city is not None:
            event.city = city
        if country is not None:
            event.country = country
        self._session.add(event)
        self._session.flush()
        self._session.refresh(event)
        return event

    def archive(self, event: Event) -> Event:
        """Archive an event logically."""
        event.status = EventStatus.ARCHIVED
        self._session.add(event)
        self._session.flush()
        self._session.refresh(event)
        return event
