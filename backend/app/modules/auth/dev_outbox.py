"""Dev-only outbox for auth emails — never active in production."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.config import Settings

logger = logging.getLogger(__name__)

_outbox: list[dict[str, str]] = []


@dataclass(frozen=True)
class DevOutboxEntry:
    """Captured dev-only auth notification."""

    kind: str
    email: str
    token: str
    path: str


def _is_dev_enabled(settings: Settings) -> bool:
    return settings.app_env in {"dev", "local"}


def record_dev_auth_link(
    *,
    settings: Settings,
    kind: str,
    email: str,
    plain_token: str,
    path: str,
) -> None:
    """Store auth link/token for local development only."""
    if not _is_dev_enabled(settings):
        return

    entry = {
        "kind": kind,
        "email": email,
        "token": plain_token,
        "path": path,
    }
    _outbox.append(entry)
    logger.info("dev_outbox %s for %s path=%s", kind, email, path)


def get_dev_outbox() -> list[dict[str, str]]:
    """Return a copy of dev outbox entries (tests/dev tooling)."""
    return list(_outbox)


def clear_dev_outbox() -> None:
    """Clear dev outbox entries."""
    _outbox.clear()
