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
