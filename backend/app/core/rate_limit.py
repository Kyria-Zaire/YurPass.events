"""In-memory rate limiter — backend-only, disableable in tests."""

from __future__ import annotations

import time
from collections import defaultdict
from threading import Lock

from fastapi import HTTPException, Request, status

from app.core.config import Settings, get_settings

_LOCK = Lock()
_BUCKETS: dict[str, list[float]] = defaultdict(list)


class RateLimitExceeded(HTTPException):
    """Raised when a client exceeds configured rate limits."""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests",
        )


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()[:64]
    if request.client:
        return request.client.host[:64]
    return "unknown"


def check_rate_limit(
    request: Request,
    *,
    limit: int,
    window_seconds: int = 60,
    email: str | None = None,
    settings: Settings | None = None,
) -> None:
    """Enforce rate limit by IP and optional email — no-op when disabled."""
    active_settings = settings or get_settings()
    if not active_settings.rate_limit_enabled:
        return

    path = request.url.path
    ip_key = f"ip:{_client_ip(request)}:{path}"
    _enforce_bucket(ip_key, limit, window_seconds)

    if email:
        normalized = email.strip().lower()
        email_key = f"email:{normalized}:{path}"
        _enforce_bucket(email_key, limit, window_seconds)


def _enforce_bucket(key: str, limit: int, window_seconds: int) -> None:
    now = time.monotonic()
    cutoff = now - window_seconds
    with _LOCK:
        timestamps = [timestamp for timestamp in _BUCKETS[key] if timestamp > cutoff]
        if len(timestamps) >= limit:
            raise RateLimitExceeded()
        timestamps.append(now)
        _BUCKETS[key] = timestamps


def reset_rate_limits() -> None:
    """Clear in-memory buckets — for tests."""
    with _LOCK:
        _BUCKETS.clear()
