"""
Fitbit OAuth 2.0 authentication service.

Handles:
- OAuth URL generation
- Token exchange
- Token refresh
- Token revocation
"""
import httpx
import base64
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from typing import Optional

from app.core.config import settings
from app.core.encryption import encrypt_token, decrypt_token
from app.core.time import get_now
from app.models.fitbit_connection import FitbitConnection


# Fitbit OAuth endpoints
FITBIT_AUTH_URL = "https://www.fitbit.com/oauth2/authorize"
FITBIT_TOKEN_URL = "https://api.fitbit.com/oauth2/token"
FITBIT_REVOKE_URL = "https://api.fitbit.com/oauth2/revoke"

# OAuth scopes
FITBIT_SCOPES = [
    "activity",
    "heartrate",
    "sleep",
    "profile"
]


def generate_auth_url(state: str) -> str:
    """
    Generate Fitbit OAuth 2.0 authorization URL.

    Args:
        state: CSRF protection state token

    Returns:
        Authorization URL to redirect user to
    """
    scope = " ".join(FITBIT_SCOPES)
    params = {
        "response_type": "code",
        "client_id": settings.fitbit_client_id,
        "redirect_uri": settings.fitbit_callback_url,
        "scope": scope,
        "state": state
    }

    # Build URL manually to ensure proper encoding
    param_str = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{FITBIT_AUTH_URL}?{param_str}"


def _get_auth_header() -> str:
    """Generate Basic Authentication header for token requests."""
    credentials = f"{settings.fitbit_client_id}:{settings.fitbit_client_secret}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return f"Basic {encoded}"


async def exchange_code_for_tokens(
    db: Session,
    code: str,
    profile_id: int
) -> FitbitConnection:
    """
    Exchange authorization code for access and refresh tokens.

    Args:
        db: Database session
        code: Authorization code from OAuth callback
        profile_id: Profile ID to associate connection with

    Returns:
        FitbitConnection record

    Raises:
        httpx.HTTPError: If token exchange fails
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            FITBIT_TOKEN_URL,
            headers={
                "Authorization": _get_auth_header(),
                "Content-Type": "application/x-www-form-urlencoded"
            },
            data={
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": settings.fitbit_callback_url
            }
        )
        response.raise_for_status()
        token_data = response.json()

    # Calculate token expiry
    expires_in = token_data.get("expires_in", 28800)  # Default 8 hours
    token_expires_at = get_now() + timedelta(seconds=expires_in)

    # Encrypt tokens before storing
    encrypted_access = encrypt_token(token_data["access_token"])
    encrypted_refresh = encrypt_token(token_data["refresh_token"])

    # Check if connection already exists (shouldn't, but handle gracefully)
    connection = db.query(FitbitConnection).filter(
        FitbitConnection.user_id == profile_id
    ).first()

    if connection:
        # Update existing connection
        connection.fitbit_user_id = token_data["user_id"]
        connection.access_token = encrypted_access
        connection.refresh_token = encrypted_refresh
        connection.token_expires_at = token_expires_at
        connection.scope = token_data["scope"]
        connection.connected_at = get_now()
    else:
        # Create new connection
        connection = FitbitConnection(
            user_id=profile_id,
            fitbit_user_id=token_data["user_id"],
            access_token=encrypted_access,
            refresh_token=encrypted_refresh,
            token_expires_at=token_expires_at,
            scope=token_data["scope"],
            connected_at=get_now()
        )
        db.add(connection)

    db.commit()
    db.refresh(connection)

    return connection


async def refresh_access_token(
    db: Session,
    connection: FitbitConnection
) -> FitbitConnection:
    """
    Refresh expired access token using refresh token.

    Args:
        db: Database session
        connection: FitbitConnection record with expired token

    Returns:
        Updated FitbitConnection record

    Raises:
        httpx.HTTPError: If token refresh fails
    """
    # Decrypt refresh token
    refresh_token = decrypt_token(connection.refresh_token)

    async with httpx.AsyncClient() as client:
        response = await client.post(
            FITBIT_TOKEN_URL,
            headers={
                "Authorization": _get_auth_header(),
                "Content-Type": "application/x-www-form-urlencoded"
            },
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token
            }
        )
        response.raise_for_status()
        token_data = response.json()

    # Calculate new token expiry
    expires_in = token_data.get("expires_in", 28800)
    token_expires_at = get_now() + timedelta(seconds=expires_in)

    # Update connection with new tokens
    connection.access_token = encrypt_token(token_data["access_token"])
    connection.refresh_token = encrypt_token(token_data["refresh_token"])
    connection.token_expires_at = token_expires_at

    db.commit()
    db.refresh(connection)

    return connection


async def revoke_token(connection: FitbitConnection) -> None:
    """
    Revoke Fitbit access token (best-effort).

    Args:
        connection: FitbitConnection record

    Note:
        This is a best-effort operation. Errors are logged but not raised.
    """
    try:
        access_token = decrypt_token(connection.access_token)

        async with httpx.AsyncClient() as client:
            await client.post(
                FITBIT_REVOKE_URL,
                headers={
                    "Authorization": _get_auth_header(),
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                data={
                    "token": access_token
                }
            )
    except Exception as e:
        # Log error but don't raise - revocation is best-effort
        print(f"Token revocation failed (non-fatal): {e}")


def is_token_expired(connection: FitbitConnection) -> bool:
    """
    Check if access token is expired or will expire soon.

    Args:
        connection: FitbitConnection record

    Returns:
        True if token is expired or will expire within 5 minutes
    """
    # Add 5-minute buffer to avoid race conditions
    buffer = timedelta(minutes=5)
    return get_now() + buffer >= connection.token_expires_at


async def ensure_valid_token(
    db: Session,
    connection: FitbitConnection
) -> FitbitConnection:
    """
    Ensure connection has a valid, non-expired access token.

    Args:
        db: Database session
        connection: FitbitConnection record

    Returns:
        FitbitConnection with valid token (may be refreshed)

    Raises:
        httpx.HTTPError: If token refresh fails
    """
    if is_token_expired(connection):
        connection = await refresh_access_token(db, connection)

    return connection
