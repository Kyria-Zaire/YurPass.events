"""Database connectivity health check (foundation — no business logic)."""

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.logging import get_logger

logger = get_logger(__name__)


def check_database(session: Session) -> bool:
    """Return True if the database responds to a simple query."""
    try:
        session.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError:
        logger.debug("Database health check failed", exc_info=True)
        return False
