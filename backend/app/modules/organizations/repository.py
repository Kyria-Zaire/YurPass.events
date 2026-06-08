"""Organizations data access — placeholder for future implementation."""

from sqlalchemy.orm import Session


class OrganizationsRepository:
    """Repository layer for Organizations module."""

    def __init__(self, session: Session) -> None:
        self._session = session
