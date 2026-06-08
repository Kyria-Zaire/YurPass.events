"""Organizations business logic."""

import uuid
from typing import Any

from app.modules.audit.constants import AuditAction
from app.modules.audit.service import AuditService
from app.modules.auth.constants import GlobalRole
from app.modules.auth.models import User
from app.modules.organizations.constants import OrganizationRole, OrganizationStatus
from app.modules.organizations.repository import (
    OrganizationMemberRepository,
    OrganizationRepository,
)
from app.modules.organizations.schemas import (
    OrganizationCreate,
    OrganizationPublic,
    OrganizationUpdate,
)
from app.modules.organizations.slug import resolve_unique_slug, slugify_name
from app.shared.exceptions import NotFoundError


class OrganizationService:
    """Service layer for Organizations module."""

    def __init__(
        self,
        organization_repository: OrganizationRepository,
        member_repository: OrganizationMemberRepository,
        audit_service: AuditService | None = None,
    ) -> None:
        self._organizations = organization_repository
        self._members = member_repository
        self._audit = audit_service

    def create(self, user: User, payload: OrganizationCreate) -> OrganizationPublic:
        """Create organization, unique slug, and active owner membership."""
        base_slug = slugify_name(payload.name)
        slug = resolve_unique_slug(base_slug, self._organizations.slug_exists)
        organization = self._organizations.create(
            name=payload.name,
            slug=slug,
            org_type=payload.type,
            created_by_user_id=user.id,
            status=OrganizationStatus.DRAFT,
            description=payload.description,
            logo_url=payload.logo_url,
            website_url=payload.website_url,
            city=payload.city,
            country=payload.country,
        )
        self._members.add_member(
            user_id=user.id,
            organization_id=organization.id,
            role=OrganizationRole.OWNER,
        )
        self._record_audit(
            AuditAction.ORGANIZATION_CREATED,
            actor_user_id=user.id,
            organization_id=organization.id,
        )
        return OrganizationPublic.model_validate(organization)

    def list_for_user(self, user: User) -> list[OrganizationPublic]:
        """List organizations visible to the user — excludes archived."""
        if user.global_role == GlobalRole.SUPER_ADMIN:
            organizations = self._organizations.list_all_non_archived()
        else:
            organizations = self._organizations.list_for_active_member(user.id)
        return [OrganizationPublic.model_validate(org) for org in organizations]

    def get(self, organization_id: uuid.UUID) -> OrganizationPublic:
        """Return organization detail — access enforced at router layer."""
        organization = self._get_organization_or_404(organization_id)
        return OrganizationPublic.model_validate(organization)

    def update(
        self,
        organization_id: uuid.UUID,
        user: User,
        payload: OrganizationUpdate,
    ) -> OrganizationPublic:
        """Update organization fields — slug remains stable."""
        organization = self._get_organization_or_404(organization_id)
        data = payload.model_dump(exclude_unset=True)
        organization = self._organizations.update(
            organization,
            name=data.get("name"),
            org_type=data.get("type"),
            description=data.get("description"),
            logo_url=data.get("logo_url"),
            website_url=data.get("website_url"),
            city=data.get("city"),
            country=data.get("country"),
        )
        self._record_audit(
            AuditAction.ORGANIZATION_UPDATED,
            actor_user_id=user.id,
            organization_id=organization.id,
            metadata={"updated_fields": sorted(data.keys())},
        )
        return OrganizationPublic.model_validate(organization)

    def archive(self, organization_id: uuid.UUID, user: User) -> OrganizationPublic:
        """Archive organization logically."""
        organization = self._get_organization_or_404(organization_id)
        organization = self._organizations.archive(organization)
        self._record_audit(
            AuditAction.ORGANIZATION_ARCHIVED,
            actor_user_id=user.id,
            organization_id=organization.id,
        )
        return OrganizationPublic.model_validate(organization)

    def _get_organization_or_404(self, organization_id: uuid.UUID):
        organization = self._organizations.get_by_id(organization_id)
        if organization is None:
            raise NotFoundError("Organization not found")
        return organization

    def _record_audit(
        self,
        action: AuditAction,
        *,
        actor_user_id: uuid.UUID,
        organization_id: uuid.UUID,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        if self._audit is None:
            return
        self._audit.record(
            action.value,
            actor_user_id=actor_user_id,
            resource_type="organization",
            resource_id=str(organization_id),
            metadata=metadata,
        )
