"""Audit log business logic."""

import uuid
from typing import Any

from app.modules.audit.models import AuditLog
from app.modules.audit.repository import AuditRepository

_FORBIDDEN_METADATA_KEYS = frozenset(
    {
        "password",
        "token",
        "refresh_token",
        "access_token",
        "plain_token",
        "otp",
        "code",
        "secret",
    }
)


def _sanitize_metadata(metadata: dict[str, Any] | None) -> dict[str, Any] | None:
    """Strip keys that may contain secrets before persisting."""
    if not metadata:
        return None
    return {
        key: value
        for key, value in metadata.items()
        if key.lower() not in _FORBIDDEN_METADATA_KEYS
    }


class AuditService:
    """Service layer for security audit events."""

    def __init__(self, repository: AuditRepository) -> None:
        self._repository = repository

    def record(
        self,
        action: str,
        *,
        actor_user_id: uuid.UUID | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditLog:
        """Record an audit event — never stores secrets in metadata."""
        return self._repository.create(
            action=action,
            actor_user_id=actor_user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=_sanitize_metadata(metadata),
        )
