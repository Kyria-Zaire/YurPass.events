"""Authentication-specific exceptions."""

from app.shared.exceptions import YurPassError


class EmailAlreadyRegisteredError(YurPassError):
    """Email is already associated with an account."""

    def __init__(self) -> None:
        super().__init__(message="Email already registered", code="email_already_registered")


class InvalidCredentialsError(YurPassError):
    """Login credentials are invalid."""

    def __init__(self) -> None:
        super().__init__(message="Invalid email or password", code="invalid_credentials")


class AccountInactiveError(YurPassError):
    """Account cannot authenticate (suspended or deleted)."""

    def __init__(self, status: str) -> None:
        super().__init__(message=f"Account is {status}", code="account_inactive")


class RefreshTokenError(YurPassError):
    """Refresh token is missing, invalid, expired, or revoked."""

    def __init__(self, message: str = "Invalid refresh token") -> None:
        super().__init__(message=message, code="invalid_refresh_token")


class AuthTokenError(YurPassError):
    """One-time auth token is invalid, expired, or already consumed."""

    def __init__(self, message: str = "Invalid or expired token") -> None:
        super().__init__(message=message, code="invalid_auth_token")


class InvalidOtpError(YurPassError):
    """OTP code is invalid, expired, or cannot be used."""

    def __init__(self) -> None:
        super().__init__(message="invalid_otp", code="invalid_otp")


class OAuthStateError(YurPassError):
    """OAuth state is missing or invalid."""

    def __init__(self) -> None:
        super().__init__(message="Invalid OAuth state", code="invalid_oauth_state")


class OAuthGoogleError(YurPassError):
    """Google OAuth flow failed."""

    def __init__(self, message: str = "Google OAuth failed") -> None:
        super().__init__(message=message, code="oauth_google_error")
