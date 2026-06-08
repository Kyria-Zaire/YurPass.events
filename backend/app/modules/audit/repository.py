"""Audit log data access."""

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.modules.audit.models import AuditLog


class AuditRepository:
    """Repository for audit log persistence."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
        self,
        *,
        action: str,
        actor_user_id: uuid.UUID | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditLog:
        """Persist a new audit log entry."""
        record = AuditLog(
            actor_user_id=actor_user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            audit_metadata=metadata,
        )
        self._session.add(record)
        self._session.flush()
        return record
