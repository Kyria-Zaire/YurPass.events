"""Password hashing utilities — Argon2id."""

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

_hasher = PasswordHasher(
    time_cost=2,
    memory_cost=65536,
    parallelism=1,
)


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password with Argon2id."""
    return _hasher.hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify a plaintext password against an Argon2id hash."""
    try:
        return _hasher.verify(password_hash, plain_password)
    except VerifyMismatchError:
        return False


_GOOGLE_OAUTH_PASSWORD_SENTINEL = "__GOOGLE_OAUTH_NO_LOCAL_PASSWORD__"


def google_oauth_password_hash() -> str:
    """Return a non-empty unusable password hash for Google-only accounts."""
    return hash_password(_GOOGLE_OAUTH_PASSWORD_SENTINEL)
