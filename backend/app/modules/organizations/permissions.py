"""Organization RBAC permission dependencies."""

from dataclasses import dataclass
from uuid import UUID

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.audit.constants import AuditAction
from app.modules.audit.repository import AuditRepository
from app.modules.audit.service import AuditService
from app.modules.auth.constants import GlobalRole
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.organizations.constants import MemberStatus, OrganizationRole
from app.modules.organizations.models import OrganizationMember
from app.modules.organizations.repository import OrganizationMemberRepository
from app.shared.exceptions import PermissionDeniedError

ORGANIZATION_ROLE_PERMISSIONS: dict[OrganizationRole, list[str]] = {
    OrganizationRole.OWNER: [
        "organization:read",
        "organization:update",
        "organization:archive",
        "member:read",
        "member:add",
        "member:update_role",
        "member:remove",
    ],
    OrganizationRole.ADMIN: [
        "organization:read",
        "organization:update",
        "member:read",
        "member:add",
    ],
    OrganizationRole.STAFF: [
        "organization:read",
        "member:read",
    ],
    OrganizationRole.VIEWER: [
        "organization:read",
    ],
}


def role_has_permission(role: OrganizationRole, permission: str) -> bool:
    """Return True when a role grants the given permission string."""
    return permission in ORGANIZATION_ROLE_PERMISSIONS.get(role, [])


@dataclass(frozen=True)
class SuperAdminOrgBypass:
    """Explicit super_admin support access — not an OrganizationMember."""

    user: User
    organization_id: UUID


@dataclass(frozen=True)
class OrgRoleAccess:
    """Resolved organization role access for a route."""

    user: User
    organization_id: UUID
    member: OrganizationMember | None
    is_super_admin_bypass: bool


def _audit_super_admin_bypass(
    db: Session,
    *,
    user: User,
    organization_id: UUID,
    allowed_roles: tuple[OrganizationRole, ...],
    permission_context: str | None = None,
) -> None:
    """Record audited super_admin organization RBAC bypass."""
    metadata: dict[str, object] = {
        "organization_id": str(organization_id),
        "requested_roles": [role.value for role in allowed_roles],
    }
    if permission_context is not None:
        metadata["permission_context"] = permission_context
    AuditService(AuditRepository(db)).record(
        AuditAction.ORGANIZATION_RBAC_SUPER_ADMIN_BYPASS.value,
        actor_user_id=user.id,
        resource_type="organization",
        resource_id=str(organization_id),
        metadata=metadata,
    )


def _get_active_member(
    repository: OrganizationMemberRepository,
    user_id: UUID,
    organization_id: UUID,
) -> OrganizationMember | None:
    """Return membership only when status is active."""
    member = repository.get_member(user_id, organization_id)
    if member is None or member.status != MemberStatus.ACTIVE:
        return None
    return member


def require_org_member(
    organization_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OrganizationMember:
    """Require an active organization membership — no super_admin bypass."""
    member = _get_active_member(
        OrganizationMemberRepository(db),
        user.id,
        organization_id,
    )
    if member is None:
        raise PermissionDeniedError()
    return member


def require_org_roles(*allowed_roles: OrganizationRole):
    """Factory returning a dependency that checks organization roles."""

    def _guard(
        organization_id: UUID,
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> OrgRoleAccess | SuperAdminOrgBypass:
        if user.global_role == GlobalRole.SUPER_ADMIN:
            _audit_super_admin_bypass(
                db,
                user=user,
                organization_id=organization_id,
                allowed_roles=allowed_roles,
            )
            return SuperAdminOrgBypass(user=user, organization_id=organization_id)

        member = _get_active_member(
            OrganizationMemberRepository(db),
            user.id,
            organization_id,
        )
        if member is None:
            raise PermissionDeniedError()
        if member.role not in allowed_roles:
            raise PermissionDeniedError()
        return OrgRoleAccess(
            user=user,
            organization_id=organization_id,
            member=member,
            is_super_admin_bypass=False,
        )

    return _guard
