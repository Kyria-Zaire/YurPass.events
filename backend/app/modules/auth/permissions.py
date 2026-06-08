"""Authentication RBAC permission dependencies."""

from fastapi import Depends

from app.modules.auth.constants import GlobalRole, UserStatus
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.shared.exceptions import PermissionDeniedError


def require_authenticated(
    user: User = Depends(get_current_user),
) -> User:
    """Require a valid authenticated user."""
    return user


def require_global_roles(*allowed_roles: GlobalRole):
    """Factory returning a dependency that checks platform global roles."""

    def _guard(user: User = Depends(get_current_user)) -> User:
        if user.global_role not in allowed_roles:
            raise PermissionDeniedError()
        return user

    return _guard


require_super_admin = require_global_roles(GlobalRole.SUPER_ADMIN)


def require_active_user(
    user: User = Depends(get_current_user),
) -> User:
    """Require an active user account."""
    if user.status != UserStatus.ACTIVE:
        raise PermissionDeniedError("Account is not active")
    return user
