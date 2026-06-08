"""Standard API response helpers."""

from typing import Any

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Standard error response shape."""

    error: str
    message: str
    details: dict[str, Any] | None = None


class HealthResponse(BaseModel):
    """Full application health check response."""

    status: str
    service: str
    version: str
    environment: str
    database: str
    redis: str
