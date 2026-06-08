"""Organizations HTTP routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.audit.repository import AuditRepository
from app.modules.audit.service import AuditService
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.auth.repository import AuthRepository
from app.modules.events.router import router as events_router
from app.modules.organizations.constants import OrganizationRole
from app.modules.organizations.member_service import OrganizationMemberService
from app.modules.organizations.permissions import (
    OrgRoleAccess,
    SuperAdminOrgBypass,
    require_active_org_member_or_super_admin,
    require_org_roles,
)
from app.modules.organizations.repository import (
    OrganizationMemberRepository,
    OrganizationRepository,
)
from app.modules.organizations.schemas import (
    OrganizationCreate,
    OrganizationMemberCreateRequest,
    OrganizationMemberListResponse,
    OrganizationMemberPublic,
    OrganizationMemberRoleUpdateRequest,
    OrganizationPublic,
    OrganizationUpdate,
)
from app.modules.organizations.service import OrganizationService

router = APIRouter()
router.include_router(
    events_router,
    prefix="/{organization_id}/events",
    tags=["events"],
)

_read_roles = (
    OrganizationRole.OWNER,
    OrganizationRole.ADMIN,
    OrganizationRole.STAFF,
    OrganizationRole.VIEWER,
)
_update_roles = (OrganizationRole.OWNER, OrganizationRole.ADMIN)
_archive_roles = (OrganizationRole.OWNER,)
_member_read_roles = (OrganizationRole.OWNER, OrganizationRole.ADMIN, OrganizationRole.STAFF)
_member_add_roles = (OrganizationRole.OWNER, OrganizationRole.ADMIN)
_member_update_roles = (OrganizationRole.OWNER,)


def get_organization_service(db: Session = Depends(get_db)) -> OrganizationService:
    """Provide OrganizationService with repositories and audit."""
    audit_service = AuditService(AuditRepository(db))
    return OrganizationService(
        OrganizationRepository(db),
        OrganizationMemberRepository(db),
        audit_service=audit_service,
    )


def get_member_service(db: Session = Depends(get_db)) -> OrganizationMemberService:
    """Provide OrganizationMemberService with repositories and audit."""
    audit_service = AuditService(AuditRepository(db))
    return OrganizationMemberService(
        OrganizationRepository(db),
        OrganizationMemberRepository(db),
        AuthRepository(db),
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


@router.get(
    "/{organization_id}/members",
    response_model=OrganizationMemberListResponse,
)
def list_organization_members(
    organization_id: UUID,
    include_inactive: bool = Query(default=False),
    access: OrgRoleAccess | SuperAdminOrgBypass = Depends(
        require_org_roles(*_member_read_roles)
    ),
    service: OrganizationMemberService = Depends(get_member_service),
) -> OrganizationMemberListResponse:
    """List organization members — active only unless owner requests inactive."""
    members = service.list_members(
        organization_id,
        include_inactive=include_inactive,
        access=access,
    )
    return OrganizationMemberListResponse(members=members)


@router.post(
    "/{organization_id}/members",
    response_model=OrganizationMemberPublic,
    status_code=status.HTTP_201_CREATED,
)
def add_organization_member(
    organization_id: UUID,
    payload: OrganizationMemberCreateRequest,
    current_user: User = Depends(get_current_user),
    _access: OrgRoleAccess | SuperAdminOrgBypass = Depends(
        require_org_roles(*_member_add_roles)
    ),
    service: OrganizationMemberService = Depends(get_member_service),
) -> OrganizationMemberPublic:
    """Add an existing user as an organization member."""
    return service.add_member(organization_id, current_user, payload)


@router.patch(
    "/{organization_id}/members/{member_id}",
    response_model=OrganizationMemberPublic,
)
def update_organization_member_role(
    organization_id: UUID,
    member_id: UUID,
    payload: OrganizationMemberRoleUpdateRequest,
    current_user: User = Depends(get_current_user),
    _access: OrgRoleAccess | SuperAdminOrgBypass = Depends(
        require_org_roles(*_member_update_roles)
    ),
    service: OrganizationMemberService = Depends(get_member_service),
) -> OrganizationMemberPublic:
    """Update a member role — owner only."""
    return service.update_member_role(organization_id, member_id, current_user, payload)


@router.delete(
    "/{organization_id}/members/{member_id}",
    response_model=OrganizationMemberPublic,
)
def remove_organization_member(
    organization_id: UUID,
    member_id: UUID,
    current_user: User = Depends(get_current_user),
    access: OrgRoleAccess | SuperAdminOrgBypass = Depends(
        require_active_org_member_or_super_admin
    ),
    service: OrganizationMemberService = Depends(get_member_service),
) -> OrganizationMemberPublic:
    """Remove a member logically or allow admin/staff/viewer self-leave."""
    return service.remove_member(
        organization_id,
        member_id,
        current_user,
        access=access,
    )
