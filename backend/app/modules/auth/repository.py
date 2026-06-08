"""Authentication data access — placeholder for future implementation."""

from sqlalchemy.orm import Session


class AuthRepository:
    """Repository layer for Authentication module."""

    def __init__(self, session: Session) -> None:
        self._session = session
