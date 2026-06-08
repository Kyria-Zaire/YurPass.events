"""Admin HTTP routes."""

from fastapi import APIRouter, Depends

from app.modules.admin.repository import AdminRepository
from app.modules.admin.schemas import RbacDiagnosticResponse
from app.modules.admin.service import AdminService
from app.modules.auth.models import User
from app.modules.auth.permissions import require_super_admin

router = APIRouter()


def get_admin_service() -> AdminService:
    """Provide AdminService — no DB access required for RBAC diagnostic."""
    return AdminService(AdminRepository())


@router.get("/rbac/diagnostic", response_model=RbacDiagnosticResponse)
def rbac_diagnostic(
    current_user: User = Depends(require_super_admin),
    service: AdminService = Depends(get_admin_service),
) -> RbacDiagnosticResponse:
    """Return global role and platform permissions for super_admin."""
    return service.get_rbac_diagnostic(current_user)
