"""Pytest fixtures."""

from collections.abc import Generator

import pytest
from app.core.config import get_settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.modules.audit.models import AuditLog  # noqa: F401
from app.modules.auth.models import AuthToken, RefreshToken, User  # noqa: F401
from app.modules.organizations.models import Organization, OrganizationMember  # noqa: F401
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker


@pytest.fixture(autouse=True)
def disable_rate_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    """Disable rate limiting for most tests."""
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "false")
    get_settings.cache_clear()


@pytest.fixture
def client() -> TestClient:
    """HTTP test client without database dependency overrides."""
    return TestClient(app)


@pytest.fixture(scope="session")
def db_engine():
    """PostgreSQL engine for integration tests — skips if unavailable."""
    settings = get_settings()
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except OperationalError as exc:
        pytest.skip(f"PostgreSQL not available: {exc}")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine) -> Generator[Session]:
    """Transactional database session rolled back after each test."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection, autocommit=False, autoflush=False)()
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def auth_client(db_session: Session) -> Generator[TestClient]:
    """HTTP client with database session override for auth endpoints."""

    def override_get_db() -> Generator[Session]:
        try:
            yield db_session
            db_session.flush()
        except Exception:
            raise

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
