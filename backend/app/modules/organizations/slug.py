"""Organization slug utilities."""

import re
import unicodedata


def slugify_name(name: str) -> str:
    """Convert an organization name to a URL-safe slug."""
    normalized = name.strip().lower()
    ascii_text = unicodedata.normalize("NFKD", normalized)
    ascii_text = ascii_text.encode("ascii", "ignore").decode("ascii")
    ascii_text = re.sub(r"[^a-z0-9\s-]", "", ascii_text)
    ascii_text = re.sub(r"[\s_]+", "-", ascii_text)
    ascii_text = re.sub(r"-+", "-", ascii_text)
    return ascii_text.strip("-")
