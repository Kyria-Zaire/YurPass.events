"""Application health check orchestration."""

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.health import check_database
from app.db.session import SessionLocal
from app.shared.responses import HealthResponse

logger = get_logger(__name__)

SERVICE_NAME = "yurpass-backend"
APP_VERSION = "0.1.0"

_ENVIRONMENT_LABELS = {
    "dev": "dev",
    "local": "dev",
    "recette": "recette",
    "preprod": "preprod",
    "production": "production",
}


def _probe_database() -> str:
    """Return connected or not_configured without exposing connection details."""
    try:
        with SessionLocal() as session:
            if check_database(session):
                return "connected"
    except Exception:
        logger.debug("Database probe unavailable", exc_info=True)
    return "not_configured"


def _probe_redis() -> str:
    """Return connected or not_configured without exposing connection details."""
    settings = get_settings()
    if not settings.redis_url:
        return "not_configured"

    try:
        import redis

        client = redis.from_url(
            settings.redis_url,
            socket_connect_timeout=1,
            socket_timeout=1,
        )
        if client.ping():
            return "connected"
    except Exception:
        logger.debug("Redis probe unavailable", exc_info=True)
    return "not_configured"


def build_health_response() -> HealthResponse:
    """Build the full application health payload."""
    settings = get_settings()
    environment = _ENVIRONMENT_LABELS.get(settings.app_env, "dev")

    return HealthResponse(
        status="ok",
        service=SERVICE_NAME,
        version=APP_VERSION,
        environment=environment,
        database=_probe_database(),
        redis=_probe_redis(),
    )
