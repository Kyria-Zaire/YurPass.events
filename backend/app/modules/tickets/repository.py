"""Tickets data access — placeholder for future implementation."""

from sqlalchemy.orm import Session


class TicketsRepository:
    """Repository layer for Tickets module."""

    def __init__(self, session: Session) -> None:
        self._session = session
