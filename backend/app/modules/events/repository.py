"""Events data access — placeholder for future implementation."""

from sqlalchemy.orm import Session


class EventsRepository:
    """Repository layer for Events module."""

    def __init__(self, session: Session) -> None:
        self._session = session
