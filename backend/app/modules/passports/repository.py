"""Passports data access — placeholder for future implementation."""

from sqlalchemy.orm import Session


class PassportsRepository:
    """Repository layer for Passports module."""

    def __init__(self, session: Session) -> None:
        self._session = session
