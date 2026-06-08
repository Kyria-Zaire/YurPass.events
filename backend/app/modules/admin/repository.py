"""Admin data access — placeholder for future implementation."""

from sqlalchemy.orm import Session


class AdminRepository:
    """Repository layer for Admin module."""

    def __init__(self, session: Session) -> None:
        self._session = session
