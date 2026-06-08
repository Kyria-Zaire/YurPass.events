"""Audit log action constants."""

from enum import StrEnum


class AuditAction(StrEnum):
    """Security-relevant actions recorded in audit_logs."""

    REGISTER_SUCCESS = "register_success"
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    REFRESH_SUCCESS = "refresh_success"
    REFRESH_FAILED = "refresh_failed"
    REFRESH_REUSE_DETECTED = "refresh_reuse_detected"
    LOGOUT = "logout"
    PASSWORD_RESET_REQUESTED = "password_reset_requested"
    PASSWORD_RESET_SUCCESS = "password_reset_success"
    EMAIL_VERIFICATION_REQUESTED = "email_verification_requested"
    EMAIL_VERIFIED = "email_verified"
    MAGIC_LINK_REQUESTED = "magic_link_requested"
    MAGIC_LINK_SUCCESS = "magic_link_success"
    OTP_REQUESTED = "otp_requested"
    OTP_SUCCESS = "otp_success"
    GOOGLE_OAUTH_SUCCESS = "google_oauth_success"
    GOOGLE_OAUTH_FAILED = "google_oauth_failed"
    ORGANIZATION_RBAC_SUPER_ADMIN_BYPASS = "organization_rbac_super_admin_bypass"
    ORGANIZATION_CREATED = "organization_created"
    ORGANIZATION_UPDATED = "organization_updated"
    ORGANIZATION_ARCHIVED = "organization_archived"
