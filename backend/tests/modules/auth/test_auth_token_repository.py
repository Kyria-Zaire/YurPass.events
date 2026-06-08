"""Auth token repository tests — AUTH-HOTFIX-003."""

from uuid import uuid4

from app.modules.auth.auth_token_repository import AuthTokenRepository
from app.modules.auth.constants import AuthTokenType, UserStatus
from app.modules.auth.models import AuthToken, User
from app.modules.auth.password import hash_password
from app.modules.auth.tokens import generate_opaque_token


def _create_user(db_session) -> User:
    user = User(
        email=f"atomic-{uuid4()}@example.com",
        password_hash=hash_password("SecurePass123!"),
        full_name="Atomic Test",
        status=UserStatus.PENDING_VERIFICATION,
    )
    db_session.add(user)
    db_session.flush()
    return user


def _create_token(db_session, user: User) -> tuple[AuthTokenRepository, AuthToken, str]:
    repo = AuthTokenRepository(db_session)
    plain = generate_opaque_token()
    record = repo.create(
        user_id=user.id,
        plain_token=plain,
        token_type=AuthTokenType.EMAIL_VERIFICATION,
    )
    return repo, record, plain


def test_consume_succeeds_for_valid_token(db_session) -> None:
    user = _create_user(db_session)
    repo, record, _plain = _create_token(db_session, user)

    assert repo.consume(record) is True
    assert record.consumed_at is not None


def test_consume_refuses_second_call_on_same_record(db_session) -> None:
    user = _create_user(db_session)
    repo, record, _plain = _create_token(db_session, user)

    assert repo.consume(record) is True
    assert repo.consume(record) is False


def test_consume_refuses_already_consumed_token(db_session) -> None:
    user = _create_user(db_session)
    repo, record, _plain = _create_token(db_session, user)

    assert repo.consume(record) is True

    stale_record = repo.get_valid_by_plain_token(_plain, AuthTokenType.EMAIL_VERIFICATION)
    assert stale_record is None
