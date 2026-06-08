"""Password hashing unit tests."""

from app.modules.auth.password import _hasher, hash_password, verify_password


def test_hash_password_returns_argon2id_hash() -> None:
    password_hash = hash_password("SecurePass123!")
    assert password_hash.startswith("$argon2id$")


def test_verify_password_accepts_correct_password() -> None:
    plain = "SecurePass123!"
    password_hash = hash_password(plain)
    assert verify_password(plain, password_hash) is True


def test_verify_password_rejects_incorrect_password() -> None:
    password_hash = hash_password("SecurePass123!")
    assert verify_password("WrongPassword!", password_hash) is False


def test_hash_password_uses_argon2id_parameters() -> None:
    password_hash = hash_password("SecurePass123!")
    assert _hasher.check_needs_rehash(password_hash) is False
