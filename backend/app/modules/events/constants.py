"""Events domain constants."""

from enum import StrEnum


class EventType(StrEnum):
    """Business category for an event."""

    NIGHTCLUB = "nightclub"
    FESTIVAL = "festival"
    CONCERT = "concert"
    CONFERENCE = "conference"
    ASSOCIATION = "association"
    SPORTS = "sports"
    OTHER = "other"


class EventStatus(StrEnum):
    """Lifecycle status for an event."""

    DRAFT = "draft"
    PUBLISHED = "published"
    SOLD_OUT = "sold_out"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class EventVisibility(StrEnum):
    """Visibility scope for an event."""

    PUBLIC = "public"
    UNLISTED = "unlisted"
    PRIVATE = "private"
