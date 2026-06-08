"""Cloudflare Turnstile verification — preparation stub for Auth V1."""

from app.core.config import Settings


class TurnstileService:
    """Verify Turnstile tokens when enabled — no-op otherwise."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def verify(self, token: str | None) -> bool:
        """Return True when Turnstile is disabled or token validation passes."""
        if not self._settings.turnstile_enabled:
            return True
        if not token:
            return False
        # Production verification will call Cloudflare API — not active in Auth V1.
        return bool(self._settings.turnstile_secret_key)
