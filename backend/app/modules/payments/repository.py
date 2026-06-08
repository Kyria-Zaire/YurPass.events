"""Payments data access — placeholder for future implementation."""

from sqlalchemy.orm import Session


class PaymentsRepository:
    """Repository layer for Payments module."""

    def __init__(self, session: Session) -> None:
        self._session = session
