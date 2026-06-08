"""Organizations data access."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.organizations.constants import OrganizationStatus, OrganizationType
from app.modules.organizations.models import Organization


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
