"""Organizations HTTP routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.audit.repository import AuditRepository
from app.modules.audit.service import AuditService
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.organizations.constants import OrganizationRole
from app.modules.organizations.permissions import (
    OrgRoleAccess,
    SuperAdminOrgBypass,
    require_org_roles,
)
from app.modules.organizations.repository import (
    OrganizationMemberRepository,
    OrganizationRepository,
)
from app.modules.organizations.schemas import (
    OrganizationCreate,
    OrganizationPublic,
    OrganizationUpdate,
)
from app.modules.organizations.service import OrganizationService

router = APIRouter()

_read_roles = (
    OrganizationRole.OWNER,
    OrganizationRole.ADMIN,
    OrganizationRole.STAFF,
    OrganizationRole.VIEWER,
)
_update_roles = (OrganizationRole.OWNER, OrganizationRole.ADMIN)
_archive_roles = (OrganizationRole.OWNER,)


def get_organization_service(db: Session = Depends(get_db)) -> OrganizationService:
    """Provide OrganizationService with repositories and audit."""
    audit_service = AuditService(AuditRepository(db))
    return OrganizationService(
        OrganizationRepository(db),
        OrganizationMemberRepository(db),
        audit_service=audit_service,
    )


@router.post(
    "",
    response_model=OrganizationPublic,
    status_code=status.HTTP_201_CREATED,
)
def create_organization(
    payload: OrganizationCreate,
    current_user: User = Depends(get_current_user),
    service: OrganizationService = Depends(get_organization_service),
) -> OrganizationPublic:
    """Create a new organization and assign the creator as owner."""
    return service.create(current_user, payload)


@router.get("", response_model=list[OrganizationPublic])
def list_organizations(
    current_user: User = Depends(get_current_user),
    service: OrganizationService = Depends(get_organization_service),
) -> list[OrganizationPublic]:
    """List organizations accessible to the current user."""
    return service.list_for_user(current_user)


@router.get("/{organization_id}", response_model=OrganizationPublic)
def get_organization(
    organization_id: UUID,
    _access: OrgRoleAccess | SuperAdminOrgBypass = Depends(require_org_roles(*_read_roles)),
    service: OrganizationService = Depends(get_organization_service),
) -> OrganizationPublic:
    """Return organization detail for active members or super_admin."""
    return service.get(organization_id)


@router.patch("/{organization_id}", response_model=OrganizationPublic)
def update_organization(
    organization_id: UUID,
    payload: OrganizationUpdate,
    current_user: User = Depends(get_current_user),
    _access: OrgRoleAccess | SuperAdminOrgBypass = Depends(require_org_roles(*_update_roles)),
    service: OrganizationService = Depends(get_organization_service),
) -> OrganizationPublic:
    """Update organization fields — slug remains stable."""
    return service.update(organization_id, current_user, payload)


@router.delete("/{organization_id}", response_model=OrganizationPublic)
def archive_organization(
    organization_id: UUID,
    current_user: User = Depends(get_current_user),
    _access: OrgRoleAccess | SuperAdminOrgBypass = Depends(require_org_roles(*_archive_roles)),
    service: OrganizationService = Depends(get_organization_service),
) -> OrganizationPublic:
    """Archive organization logically."""
    return service.archive(organization_id, current_user)
