"""Organizations-specific exceptions."""

from app.shared.exceptions import PermissionDeniedError, YurPassError


class ConflictError(YurPassError):
    """Base for organization conflict responses (HTTP 409)."""


class MemberAlreadyExistsError(ConflictError):
    """Active membership already exists for this user."""

    def __init__(self) -> None:
        super().__init__(
            message="Member already exists for this organization",
            code="member_already_exists",
        )


class MemberInactiveRequiresManualReactivationError(ConflictError):
    """Inactive membership cannot be reactivated via members API."""

    def __init__(self) -> None:
        super().__init__(
            message="Inactive member requires manual reactivation",
            code="member_inactive_requires_manual_reactivation",
        )


class LastOwnerProtectedError(ConflictError):
    """Operation would remove or demote the last active owner."""

    def __init__(self) -> None:
        super().__init__(
            message="Cannot modify or remove the last active owner",
            code="last_owner_protected",
        )


class OwnerRoleNotAllowedError(ConflictError):
    """Owner role cannot be assigned via members API."""

    def __init__(self) -> None:
        super().__init__(
            message="Owner role cannot be assigned via members API",
            code="owner_role_not_allowed",
        )


class OwnerSelfLeaveForbiddenError(PermissionDeniedError):
    """Owners cannot voluntarily leave an organization."""

    def __init__(self) -> None:
        super().__init__("Owners cannot self-leave an organization")
        self.code = "owner_self_leave_forbidden"
