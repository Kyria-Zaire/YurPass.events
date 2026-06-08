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


class AuthTokenType(StrEnum):
    """Opaque one-time auth token purposes."""

    EMAIL_VERIFICATION = "email_verification"
    PASSWORD_RESET = "password_reset"
    MAGIC_LINK = "magic_link"


EMAIL_VERIFICATION_EXPIRE_HOURS = 24
PASSWORD_RESET_EXPIRE_MINUTES = 30
MAGIC_LINK_EXPIRE_MINUTES = 15
