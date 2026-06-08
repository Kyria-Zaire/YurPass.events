"""Admin Pydantic schemas."""

from pydantic import BaseModel, Field


class RbacDiagnosticResponse(BaseModel):
    """RBAC diagnostic payload for super_admin."""

    global_role: str
    permissions: list[str] = Field(default_factory=list)
