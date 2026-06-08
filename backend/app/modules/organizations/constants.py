"""Organizations domain constants."""

from enum import StrEnum


class OrganizationType(StrEnum):
    """Business category for an organization."""

    NIGHTCLUB = "nightclub"
    FESTIVAL = "festival"
    ASSOCIATION = "association"
    BDE = "bde"
    VENUE = "venue"
    BUSINESS = "business"
    INDEPENDENT_ORGANIZER = "independent_organizer"
    OTHER = "other"


class OrganizationStatus(StrEnum):
    """Lifecycle status for an organization."""

    DRAFT = "draft"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"


class OrganizationRole(StrEnum):
    """Organization-scoped role for a member."""

    OWNER = "owner"
    ADMIN = "admin"
    STAFF = "staff"
    VIEWER = "viewer"


class MemberStatus(StrEnum):
    """Lifecycle status for an organization membership."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    LEFT = "left"
