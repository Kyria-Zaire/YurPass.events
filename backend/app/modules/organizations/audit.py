"""Organization audit helpers — TICKET-007F."""

import uuid
from typing import Any

from app.modules.audit.constants import AuditAction
from app.modules.audit.service import AuditService
from app.modules.auth.constants import GlobalRole
from app.modules.auth.models import User
from app.modules.organizations.constants import MemberStatus
from app.modules.organizations.permissions import OrgRoleAccess, SuperAdminOrgBypass
from app.modules.organizations.repository import OrganizationMemberRepository

SUPER_ADMIN_ACTOR_ROLE = "super_admin"


def resolve_actor_role(
    user: User,
    organization_id: uuid.UUID,
    member_repository: OrganizationMemberRepository,
    *,
    access: OrgRoleAccess | SuperAdminOrgBypass | None = None,
) -> str:
    """Resolve organization-scoped actor role for audit metadata."""
    if access is not None and isinstance(access, SuperAdminOrgBypass):
        return SUPER_ADMIN_ACTOR_ROLE
    if access is not None and access.member is not None:
        return access.member.role.value

    member = member_repository.get_member(user.id, organization_id)
    if member is not None and member.status == MemberStatus.ACTIVE:
        return member.role.value
    if user.global_role == GlobalRole.SUPER_ADMIN:
        return SUPER_ADMIN_ACTOR_ROLE
    return "unknown"


def record_organization_audit(
    audit_service: AuditService | None,
    action: AuditAction,
    *,
    actor_user_id: uuid.UUID,
    organization_id: uuid.UUID,
    actor_role: str,
    extra_metadata: dict[str, Any] | None = None,
) -> None:
    """Record an organization-scoped audit event."""
    if audit_service is None:
        return
    metadata: dict[str, Any] = {
        "organization_id": str(organization_id),
        "actor_role": actor_role,
    }
    if extra_metadata:
        metadata.update(extra_metadata)
    audit_service.record(
        action.value,
        actor_user_id=actor_user_id,
        resource_type="organization",
        resource_id=str(organization_id),
        metadata=metadata,
    )


def record_member_audit(
    audit_service: AuditService | None,
    action: AuditAction,
    *,
    actor_user_id: uuid.UUID,
    organization_id: uuid.UUID,
    member_id: uuid.UUID,
    actor_role: str,
    target_user_id: uuid.UUID,
    extra_metadata: dict[str, Any] | None = None,
) -> None:
    """Record an organization member audit event — organization_id always in metadata."""
    if audit_service is None:
        return
    metadata: dict[str, Any] = {
        "organization_id": str(organization_id),
        "actor_role": actor_role,
        "target_user_id": str(target_user_id),
    }
    if extra_metadata:
        metadata.update(extra_metadata)
    audit_service.record(
        action.value,
        actor_user_id=actor_user_id,
        resource_type="organization_member",
        resource_id=str(member_id),
        metadata=metadata,
    )
