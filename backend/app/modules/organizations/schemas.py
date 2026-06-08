"""Organizations Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.organizations.constants import (
    MemberStatus,
    OrganizationRole,
    OrganizationStatus,
    OrganizationType,
)


class OrganizationBase(BaseModel):
    """Shared organization fields."""

    name: str = Field(min_length=1, max_length=255)
    type: OrganizationType
    description: str | None = None
    logo_url: str | None = Field(default=None, max_length=2048)
    website_url: str | None = Field(default=None, max_length=2048)
    city: str | None = Field(default=None, max_length=255)
    country: str | None = Field(default=None, max_length=2)


class OrganizationCreate(OrganizationBase):
    """Payload for creating an organization — slug resolved in later tickets."""


class OrganizationUpdate(BaseModel):
    """Payload for partial organization updates."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    type: OrganizationType | None = None
    description: str | None = None
    logo_url: str | None = Field(default=None, max_length=2048)
    website_url: str | None = Field(default=None, max_length=2048)
    city: str | None = Field(default=None, max_length=255)
    country: str | None = Field(default=None, max_length=2)


class OrganizationPublic(OrganizationBase):
    """Public organization representation."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    status: OrganizationStatus
    created_by_user_id: UUID
    created_at: datetime
    updated_at: datetime


class OrganizationMemberCreateRequest(BaseModel):
    """Payload for POST /members — existing user only."""

    user_id: UUID
    role: OrganizationRole


class OrganizationMemberRoleUpdateRequest(BaseModel):
    """Payload for PATCH /members/{member_id} — role only."""

    role: OrganizationRole


class OrganizationMemberListResponse(BaseModel):
    """List of organization members."""

    members: list["OrganizationMemberPublic"]


class OrganizationMemberPublic(BaseModel):
    """Public organization member representation."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    organization_id: UUID
    role: OrganizationRole
    status: MemberStatus
    created_at: datetime
    updated_at: datetime
