"""Organization members business logic — TICKET-007E."""

import uuid
from typing import Any

from app.modules.audit.constants import AuditAction
from app.modules.audit.service import AuditService
from app.modules.auth.constants import GlobalRole
from app.modules.auth.models import User
from app.modules.auth.repository import AuthRepository
from app.modules.organizations.constants import MemberStatus, OrganizationRole
from app.modules.organizations.exceptions import (
    LastOwnerProtectedError,
    MemberAlreadyExistsError,
    MemberInactiveRequiresManualReactivationError,
    OwnerRoleNotAllowedError,
    OwnerSelfLeaveForbiddenError,
)
from app.modules.organizations.permissions import OrgRoleAccess, SuperAdminOrgBypass
from app.modules.organizations.repository import (
    OrganizationMemberRepository,
    OrganizationRepository,
)
from app.modules.organizations.schemas import (
    OrganizationMemberCreateRequest,
    OrganizationMemberPublic,
    OrganizationMemberRoleUpdateRequest,
)
from app.shared.exceptions import NotFoundError, PermissionDeniedError

_ASSIGNABLE_ROLES = frozenset(
    {
        OrganizationRole.ADMIN,
        OrganizationRole.STAFF,
        OrganizationRole.VIEWER,
    }
)


class OrganizationMemberService:
    """Service layer for organization member management."""

    def __init__(
        self,
        organization_repository: OrganizationRepository,
        member_repository: OrganizationMemberRepository,
        auth_repository: AuthRepository,
        audit_service: AuditService | None = None,
    ) -> None:
        self._organizations = organization_repository
        self._members = member_repository
        self._users = auth_repository
        self._audit = audit_service

    def list_members(
        self,
        organization_id: uuid.UUID,
        *,
        include_inactive: bool,
        access: OrgRoleAccess | SuperAdminOrgBypass,
    ) -> list[OrganizationMemberPublic]:
        """List members — active only by default; inactive requires owner."""
        self._ensure_organization_exists(organization_id)
        if include_inactive:
            self._require_owner_or_super_admin(access, organization_id)
            members = self._members.list_members(organization_id)
        else:
            members = self._members.list_active_members(organization_id)
        return [OrganizationMemberPublic.model_validate(member) for member in members]

    def add_member(
        self,
        organization_id: uuid.UUID,
        actor: User,
        payload: OrganizationMemberCreateRequest,
    ) -> OrganizationMemberPublic:
        """Add an existing user as an active organization member."""
        self._ensure_organization_exists(organization_id)
        self._validate_assignable_role(payload.role)

        target_user = self._users.get_by_id(payload.user_id)
        if target_user is None:
            raise NotFoundError("User not found")

        existing = self._members.get_member(payload.user_id, organization_id)
        if existing is not None:
            if existing.status == MemberStatus.ACTIVE:
                raise MemberAlreadyExistsError()
            raise MemberInactiveRequiresManualReactivationError()

        member = self._members.add_member(
            user_id=payload.user_id,
            organization_id=organization_id,
            role=payload.role,
        )
        self._record_audit(
            AuditAction.ORGANIZATION_MEMBER_ADDED,
            actor_user_id=actor.id,
            organization_id=organization_id,
            member_id=member.id,
            metadata={"user_id": str(payload.user_id), "role": payload.role.value},
        )
        return OrganizationMemberPublic.model_validate(member)

    def update_member_role(
        self,
        organization_id: uuid.UUID,
        member_id: uuid.UUID,
        actor: User,
        payload: OrganizationMemberRoleUpdateRequest,
    ) -> OrganizationMemberPublic:
        """Update a member role — owner only, no owner promotion."""
        self._ensure_organization_exists(organization_id)
        self._validate_assignable_role(payload.role)

        member = self._get_member_or_404(member_id, organization_id)
        if member.status != MemberStatus.ACTIVE:
            raise NotFoundError("Member not found")

        if (
            member.role == OrganizationRole.OWNER
            and self._members.count_active_owners(organization_id) <= 1
        ):
            raise LastOwnerProtectedError()
        if payload.role == member.role:
            return OrganizationMemberPublic.model_validate(member)

        previous_role = member.role
        member = self._members.update_member_role(member, payload.role)
        self._record_audit(
            AuditAction.ORGANIZATION_MEMBER_ROLE_UPDATED,
            actor_user_id=actor.id,
            organization_id=organization_id,
            member_id=member.id,
            metadata={
                "user_id": str(member.user_id),
                "previous_role": previous_role.value,
                "new_role": payload.role.value,
            },
        )
        return OrganizationMemberPublic.model_validate(member)

    def remove_member(
        self,
        organization_id: uuid.UUID,
        member_id: uuid.UUID,
        actor: User,
        *,
        access: OrgRoleAccess | SuperAdminOrgBypass,
    ) -> OrganizationMemberPublic:
        """Remove a member logically (status=left) with owner protection."""
        self._ensure_organization_exists(organization_id)
        target = self._get_member_or_404(member_id, organization_id)
        if target.status != MemberStatus.ACTIVE:
            raise NotFoundError("Member not found")

        actor_member = self._resolve_actor_member(access, organization_id)
        is_self_leave = actor_member is not None and actor_member.id == target.id

        if is_self_leave:
            if target.role == OrganizationRole.OWNER:
                raise OwnerSelfLeaveForbiddenError()
        elif not self._actor_is_owner_or_super_admin(access, actor_member):
            raise PermissionDeniedError()
        elif (
            target.role == OrganizationRole.OWNER
            and self._members.count_active_owners(organization_id) <= 1
        ):
            raise LastOwnerProtectedError()

        member = self._members.update_member_status(target, MemberStatus.LEFT)
        self._record_audit(
            AuditAction.ORGANIZATION_MEMBER_REMOVED,
            actor_user_id=actor.id,
            organization_id=organization_id,
            member_id=member.id,
            metadata={
                "user_id": str(member.user_id),
                "role": member.role.value,
                "self_leave": is_self_leave,
            },
        )
        return OrganizationMemberPublic.model_validate(member)

    def _ensure_organization_exists(self, organization_id: uuid.UUID) -> None:
        if self._organizations.get_by_id(organization_id) is None:
            raise NotFoundError("Organization not found")

    def _get_member_or_404(
        self,
        member_id: uuid.UUID,
        organization_id: uuid.UUID,
    ):
        member = self._members.get_member_by_id_and_org(member_id, organization_id)
        if member is None:
            raise NotFoundError("Member not found")
        return member

    @staticmethod
    def _validate_assignable_role(role: OrganizationRole) -> None:
        if role == OrganizationRole.OWNER:
            raise OwnerRoleNotAllowedError()
        if role not in _ASSIGNABLE_ROLES:
            raise OwnerRoleNotAllowedError()

    @staticmethod
    def _require_owner_or_super_admin(
        access: OrgRoleAccess | SuperAdminOrgBypass,
        organization_id: uuid.UUID,
    ) -> None:
        if isinstance(access, SuperAdminOrgBypass):
            if access.organization_id != organization_id:
                raise PermissionDeniedError()
            return
        if access.member is None or access.member.role != OrganizationRole.OWNER:
            raise PermissionDeniedError()

    @staticmethod
    def _resolve_actor_member(
        access: OrgRoleAccess | SuperAdminOrgBypass,
        organization_id: uuid.UUID,
    ):
        if isinstance(access, SuperAdminOrgBypass):
            return None
        if access.organization_id != organization_id:
            raise PermissionDeniedError()
        return access.member

    @staticmethod
    def _actor_is_owner_or_super_admin(
        access: OrgRoleAccess | SuperAdminOrgBypass,
        actor_member,
    ) -> bool:
        if isinstance(access, SuperAdminOrgBypass):
            return access.user.global_role == GlobalRole.SUPER_ADMIN
        return actor_member is not None and actor_member.role == OrganizationRole.OWNER

    def _record_audit(
        self,
        action: AuditAction,
        *,
        actor_user_id: uuid.UUID,
        organization_id: uuid.UUID,
        member_id: uuid.UUID,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        if self._audit is None:
            return
        self._audit.record(
            action.value,
            actor_user_id=actor_user_id,
            resource_type="organization_member",
            resource_id=str(member_id),
            metadata={
                "organization_id": str(organization_id),
                **(metadata or {}),
            },
        )
