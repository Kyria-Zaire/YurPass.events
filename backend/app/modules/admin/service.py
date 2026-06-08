"""Admin business logic."""

from app.modules.admin.repository import AdminRepository
from app.modules.admin.schemas import RbacDiagnosticResponse
from app.modules.auth.models import User


class AdminService:
    """Service layer for Admin module."""

    def __init__(self, repository: AdminRepository) -> None:
        self._repository = repository

    def get_rbac_diagnostic(self, user: User) -> RbacDiagnosticResponse:
        """Build RBAC diagnostic for the authenticated super_admin."""
        permissions = self._repository.get_platform_permissions(user.global_role)
        return RbacDiagnosticResponse(
            global_role=user.global_role.value,
            permissions=permissions,
        )
