"""Admin data access."""

from app.modules.admin.permissions import PLATFORM_PERMISSIONS
from app.modules.auth.constants import GlobalRole


class AdminRepository:
    """Repository layer for Admin module."""

    def get_platform_permissions(self, role: GlobalRole) -> list[str]:
        """Return platform permissions granted to a global role."""
        return list(PLATFORM_PERMISSIONS.get(role, []))
