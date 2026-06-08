"""Event slug utilities."""

import re
import unicodedata
from collections.abc import Callable


def slugify_name(name: str) -> str:
    """Convert an event name to a URL-safe slug."""
    normalized = name.strip().lower()
    ascii_text = unicodedata.normalize("NFKD", normalized)
    ascii_text = ascii_text.encode("ascii", "ignore").decode("ascii")
    ascii_text = re.sub(r"[^a-z0-9\s-]", "", ascii_text)
    ascii_text = re.sub(r"[\s_]+", "-", ascii_text)
    ascii_text = re.sub(r"-+", "-", ascii_text)
    return ascii_text.strip("-") or "event"


def resolve_unique_slug(base_slug: str, slug_exists: Callable[[str], bool]) -> str:
    """Return a globally unique slug, appending -2, -3, ... on collision."""
    if not slug_exists(base_slug):
        return base_slug
    counter = 2
    while slug_exists(f"{base_slug}-{counter}"):
        counter += 1
    return f"{base_slug}-{counter}"
