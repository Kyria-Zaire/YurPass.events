"""Organizations data access."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.organizations.constants import (
    MemberStatus,
    OrganizationRole,
    OrganizationStatus,
    OrganizationType,
)
from app.modules.organizations.models import Organization, OrganizationMember


class OrganizationRepository:
    """Repository layer for Organization persistence."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, organization_id: uuid.UUID) -> Organization | None:
        """Return an organization by primary key."""
        return self._session.get(Organization, organization_id)

    def get_by_slug(self, slug: str) -> Organization | None:
        """Return an organization by unique slug."""
        statement = select(Organization).where(Organization.slug == slug)
        return self._session.scalar(statement)

    def slug_exists(self, slug: str) -> bool:
        """Return True when a slug is already taken."""
        return self.get_by_slug(slug) is not None

    def create(
        self,
        *,
        name: str,
        slug: str,
        org_type: OrganizationType,
        created_by_user_id: uuid.UUID,
        status: OrganizationStatus = OrganizationStatus.DRAFT,
        description: str | None = None,
        logo_url: str | None = None,
        website_url: str | None = None,
        city: str | None = None,
        country: str | None = None,
    ) -> Organization:
        """Persist a new organization."""
        organization = Organization(
            name=name,
            slug=slug,
            type=org_type,
            status=status,
            description=description,
            logo_url=logo_url,
            website_url=website_url,
            city=city,
            country=country,
            created_by_user_id=created_by_user_id,
        )
        self._session.add(organization)
        self._session.flush()
        self._session.refresh(organization)
        return organization


class OrganizationMemberRepository:
    """Repository layer for OrganizationMember persistence."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_member_by_id(self, member_id: uuid.UUID) -> OrganizationMember | None:
        """Return a membership by primary key."""
        return self._session.get(OrganizationMember, member_id)

    def get_member(
        self,
        user_id: uuid.UUID,
        organization_id: uuid.UUID,
    ) -> OrganizationMember | None:
        """Return a membership for a user within an organization."""
        statement = select(OrganizationMember).where(
            OrganizationMember.user_id == user_id,
            OrganizationMember.organization_id == organization_id,
        )
        return self._session.scalar(statement)

    def list_members(self, organization_id: uuid.UUID) -> list[OrganizationMember]:
        """List all members for an organization."""
        statement = (
            select(OrganizationMember)
            .where(OrganizationMember.organization_id == organization_id)
            .order_by(OrganizationMember.created_at)
        )
        return list(self._session.scalars(statement))

    def add_member(
        self,
        *,
        user_id: uuid.UUID,
        organization_id: uuid.UUID,
        role: OrganizationRole,
        status: MemberStatus = MemberStatus.ACTIVE,
    ) -> OrganizationMember:
        """Create a new organization membership."""
        member = OrganizationMember(
            user_id=user_id,
            organization_id=organization_id,
            role=role,
            status=status,
        )
        self._session.add(member)
        self._session.flush()
        self._session.refresh(member)
        return member

    def update_member_role(
        self,
        member: OrganizationMember,
        role: OrganizationRole,
    ) -> OrganizationMember:
        """Update a member's organization role."""
        member.role = role
        self._session.add(member)
        self._session.flush()
        self._session.refresh(member)
        return member

    def update_member_status(
        self,
        member: OrganizationMember,
        status: MemberStatus,
    ) -> OrganizationMember:
        """Update a member's membership status."""
        member.status = status
        self._session.add(member)
        self._session.flush()
        self._session.refresh(member)
        return member

    def count_active_owners(self, organization_id: uuid.UUID) -> int:
        """Count active owners for an organization."""
        statement = select(func.count()).select_from(OrganizationMember).where(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.role == OrganizationRole.OWNER,
            OrganizationMember.status == MemberStatus.ACTIVE,
        )
        return int(self._session.scalar(statement) or 0)
