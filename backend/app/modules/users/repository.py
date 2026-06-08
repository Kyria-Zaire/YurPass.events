"""Users data access — placeholder for future implementation."""

from sqlalchemy.orm import Session


class UsersRepository:
    """Repository layer for Users module."""

    def __init__(self, session: Session) -> None:
        self._session = session
