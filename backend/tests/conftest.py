"""Pytest fixtures."""

import pytest
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> TestClient:
    """HTTP test client for the FastAPI application."""
    return TestClient(app)
