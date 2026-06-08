"""Invitations data access — placeholder for future implementation."""

from sqlalchemy.orm import Session


class InvitationsRepository:
    """Repository layer for Invitations module."""

    def __init__(self, session: Session) -> None:
        self._session = session
