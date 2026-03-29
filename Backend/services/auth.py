from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import jwt
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from jwt import InvalidTokenError

from config import settings


class AuthError(Exception):
    """Authentication/authorization error with a stable API error code."""


def verify_google_id_token(token: str) -> Dict[str, Any]:
    """Verify Google ID token and return claims."""
    if not settings.google_client_id:
        raise AuthError("GOOGLE_OAUTH_NOT_CONFIGURED")

    try:
        claims = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            settings.google_client_id,
        )
    except Exception as exc:  # Google SDK exposes multiple token exceptions.
        raise AuthError("INVALID_GOOGLE_TOKEN") from exc

    if claims.get("iss") not in {"accounts.google.com", "https://accounts.google.com"}:
        raise AuthError("INVALID_GOOGLE_TOKEN")

    if not claims.get("email_verified", False):
        raise AuthError("EMAIL_NOT_VERIFIED")

    return claims


def create_access_token(user_id: str, email: str) -> str:
    """Create a signed JWT access token for API authorization."""
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expires_minutes)
    payload = {
        "sub": user_id,
        "email": email,
        "exp": expires_at,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and validate API JWT."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except InvalidTokenError as exc:
        raise AuthError("INVALID_AUTH_TOKEN") from exc
    return payload
