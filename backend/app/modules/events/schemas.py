"""Events Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.events.constants import EventStatus, EventType, EventVisibility


class EventBase(BaseModel):
    """Shared event fields."""

    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    event_type: EventType
    visibility: EventVisibility = EventVisibility.PUBLIC
    starts_at: datetime
    ends_at: datetime
    cover_image_url: str | None = Field(default=None, max_length=2048)
    venue_name: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=255)
    country: str | None = Field(default=None, max_length=255)


class EventCreate(EventBase):
    """Payload for creating an event — slug resolved in later tickets."""


class EventUpdate(BaseModel):
    """Payload for partial event updates."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    event_type: EventType | None = None
    visibility: EventVisibility | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    cover_image_url: str | None = Field(default=None, max_length=2048)
    venue_name: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=255)
    country: str | None = Field(default=None, max_length=255)


class EventPublic(EventBase):
    """Public event representation."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    slug: str
    status: EventStatus
    created_by_user_id: UUID
    created_at: datetime
    updated_at: datetime
