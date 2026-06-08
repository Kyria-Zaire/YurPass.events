"""Events HTTP routes — nested under organizations."""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.events.repository import EventRepository
from app.modules.events.schemas import EventCreate, EventPublic, EventUpdate
from app.modules.events.service import EventService
from app.modules.organizations.constants import OrganizationRole
from app.modules.organizations.permissions import (
    OrgRoleAccess,
    SuperAdminOrgBypass,
    require_org_roles,
)
from app.modules.organizations.repository import OrganizationRepository

router = APIRouter()

_read_roles = (OrganizationRole.OWNER, OrganizationRole.ADMIN, OrganizationRole.STAFF)
_write_roles = (OrganizationRole.OWNER, OrganizationRole.ADMIN)


def get_event_service(db: Session = Depends(get_db)) -> EventService:
    """Provide EventService with repositories."""
    return EventService(
        EventRepository(db),
        OrganizationRepository(db),
    )


@router.post(
    "",
    response_model=EventPublic,
    status_code=status.HTTP_201_CREATED,
)
def create_event(
    organization_id: UUID,
    payload: EventCreate,
    current_user: User = Depends(get_current_user),
    _access: OrgRoleAccess | SuperAdminOrgBypass = Depends(require_org_roles(*_write_roles)),
    service: EventService = Depends(get_event_service),
) -> EventPublic:
    """Create a draft event for an organization."""
    return service.create(organization_id, current_user, payload)


@router.get("", response_model=list[EventPublic])
def list_events(
    organization_id: UUID,
    _access: OrgRoleAccess | SuperAdminOrgBypass = Depends(require_org_roles(*_read_roles)),
    service: EventService = Depends(get_event_service),
) -> list[EventPublic]:
    """List non-archived events for an organization."""
    return service.list_for_organization(organization_id)


@router.get("/{event_id}", response_model=EventPublic)
def get_event(
    organization_id: UUID,
    event_id: UUID,
    _access: OrgRoleAccess | SuperAdminOrgBypass = Depends(require_org_roles(*_read_roles)),
    service: EventService = Depends(get_event_service),
) -> EventPublic:
    """Return event detail for organization members."""
    return service.get(organization_id, event_id)


@router.patch("/{event_id}", response_model=EventPublic)
def update_event(
    organization_id: UUID,
    event_id: UUID,
    payload: EventUpdate,
    _access: OrgRoleAccess | SuperAdminOrgBypass = Depends(require_org_roles(*_write_roles)),
    service: EventService = Depends(get_event_service),
) -> EventPublic:
    """Update event fields — slug remains stable."""
    return service.update(organization_id, event_id, payload)


@router.delete("/{event_id}", response_model=EventPublic)
def archive_event(
    organization_id: UUID,
    event_id: UUID,
    _access: OrgRoleAccess | SuperAdminOrgBypass = Depends(require_org_roles(*_write_roles)),
    service: EventService = Depends(get_event_service),
) -> EventPublic:
    """Archive an event logically."""
    return service.archive(organization_id, event_id)
