"""YurPass FastAPI application entry point."""

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.health import build_health_response
from app.core.logging import setup_logging
from app.shared.responses import HealthResponse

setup_logging()
settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
)


@app.get("/api/health", response_model=HealthResponse, tags=["health"])
def api_health() -> HealthResponse:
    """Application health probe — stable without mandatory DB/Redis."""
    return build_health_response()
