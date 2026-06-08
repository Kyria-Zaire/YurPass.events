"""Authentication domain constants."""

from enum import StrEnum


class UserStatus(StrEnum):
    """Lifecycle status for a user account."""

    ACTIVE = "active"
    PENDING_VERIFICATION = "pending_verification"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class GlobalRole(StrEnum):
    """Platform-wide role carried by User (not organization-specific)."""

    USER = "user"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"
