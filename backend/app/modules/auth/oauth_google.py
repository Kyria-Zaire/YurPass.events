"""Google OAuth 2.0 Authorization Code Flow client."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING
from urllib.parse import urlencode

import httpx

from app.modules.auth.exceptions import OAuthGoogleError

if TYPE_CHECKING:
    from app.core.config import Settings

GOOGLE_OAUTH_SCOPES = "openid email profile"


@dataclass(frozen=True)
class GoogleUserInfo:
    """Minimal validated Google userinfo payload."""

    sub: str
    email: str
    email_verified: bool
    name: str | None = None
    picture: str | None = None


class GoogleOAuthClient:
    """Server-side Google OAuth helper — no token persistence."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def build_authorization_url(self, state: str) -> str:
        """Build Google authorization URL for Authorization Code Flow."""
        params = {
            "client_id": self._settings.google_client_id,
            "redirect_uri": self._settings.google_redirect_uri,
            "response_type": "code",
            "scope": GOOGLE_OAUTH_SCOPES,
            "state": state,
            "access_type": "online",
            "include_granted_scopes": "true",
        }
        return f"{self._settings.google_auth_url}?{urlencode(params)}"

    def authenticate_with_code(self, code: str) -> GoogleUserInfo:
        """Exchange code for userinfo — Google access token is not stored."""
        access_token = self._exchange_code_for_access_token(code)
        return self._fetch_userinfo(access_token)

    def _exchange_code_for_access_token(self, code: str) -> str:
        try:
            response = httpx.post(
                self._settings.google_token_url,
                data={
                    "code": code,
                    "client_id": self._settings.google_client_id,
                    "client_secret": self._settings.google_client_secret,
                    "redirect_uri": self._settings.google_redirect_uri,
                    "grant_type": "authorization_code",
                },
                timeout=10.0,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise OAuthGoogleError("Failed to exchange Google authorization code") from exc

        payload = response.json()
        access_token = payload.get("access_token")
        if not isinstance(access_token, str) or not access_token:
            raise OAuthGoogleError("Missing access token from Google")
        return access_token

    def _fetch_userinfo(self, access_token: str) -> GoogleUserInfo:
        try:
            response = httpx.get(
                self._settings.google_userinfo_url,
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10.0,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise OAuthGoogleError("Failed to fetch Google userinfo") from exc

        return parse_google_userinfo(response.json())


def parse_google_userinfo(payload: dict) -> GoogleUserInfo:
    """Validate and normalize Google userinfo response."""
    sub = payload.get("sub")
    email = payload.get("email")
    email_verified = payload.get("email_verified")

    if not isinstance(sub, str) or not sub:
        raise OAuthGoogleError("Missing Google subject")
    if not isinstance(email, str) or not email:
        raise OAuthGoogleError("Missing Google email")
    if email_verified is not True:
        raise OAuthGoogleError("Google email not verified")

    name = payload.get("name")
    picture = payload.get("picture")
    return GoogleUserInfo(
        sub=sub,
        email=email.strip().lower(),
        email_verified=True,
        name=name if isinstance(name, str) else None,
        picture=picture if isinstance(picture, str) else None,
    )
