"""Application exception hierarchy (foundation placeholders)."""


class YurPassError(Exception):
    """Base exception for YurPass backend."""

    def __init__(self, message: str, code: str = "internal_error") -> None:
        self.message = message
        self.code = code
        super().__init__(message)


class NotFoundError(YurPassError):
    """Resource not found."""

    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message=message, code="not_found")


class ValidationError(YurPassError):
    """Validation failed."""

    def __init__(self, message: str = "Validation failed") -> None:
        super().__init__(message=message, code="validation_error")


class PermissionDeniedError(YurPassError):
    """Permission denied."""

    def __init__(self, message: str = "Permission denied") -> None:
        super().__init__(message=message, code="permission_denied")
