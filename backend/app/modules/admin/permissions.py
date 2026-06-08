"""Platform-wide permission map for global roles."""

from app.modules.auth.constants import GlobalRole

PLATFORM_PERMISSIONS: dict[GlobalRole, list[str]] = {
    GlobalRole.USER: [],
    GlobalRole.ADMIN: ["admin.access"],
    GlobalRole.SUPER_ADMIN: [
        "admin.access",
        "admin.rbac.diagnostic",
        "admin.users.manage",
    ],
}
