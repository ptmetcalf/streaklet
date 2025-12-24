"""Tests for Fitbit OAuth service."""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
from sqlalchemy.orm import Session

from app.services import fitbit_oauth
from app.models.fitbit_connection import FitbitConnection
from app.core.time import get_now


def test_generate_auth_url():
    """Test OAuth authorization URL generation."""
    state = "test_state_token"
    url = fitbit_oauth.generate_auth_url(state)

    assert "https://www.fitbit.com/oauth2/authorize" in url
    assert "response_type=code" in url
    assert f"state={state}" in url
    assert "scope=activity heartrate sleep profile" in url


@pytest.mark.asyncio
async def test_exchange_code_for_tokens(test_db: Session, sample_profiles):
    """Test exchanging authorization code for tokens."""
    mock_response = AsyncMock()
    mock_response.json = AsyncMock(return_value={
        "access_token": "test_access_token",
        "refresh_token": "test_refresh_token",
        "user_id": "FITBIT123",
        "scope": "activity heartrate sleep profile",
        "expires_in": 28800
    })
    mock_response.raise_for_status = AsyncMock()

    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = AsyncMock()
        mock_instance.post = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__.return_value = mock_instance

        connection = await fitbit_oauth.exchange_code_for_tokens(
            test_db,
            code="test_code",
            profile_id=1
        )

    assert connection.user_id == 1
    assert connection.fitbit_user_id == "FITBIT123"
    assert connection.scope == "activity heartrate sleep profile"
    # Tokens should be encrypted
    assert connection.access_token != "test_access_token"
    assert connection.refresh_token != "test_refresh_token"


@pytest.mark.asyncio
async def test_exchange_code_updates_existing_connection(test_db: Session, sample_profiles):
    """Test that exchanging code updates existing connection instead of creating new one."""
    # Create existing connection
    existing = FitbitConnection(
        user_id=1,
        fitbit_user_id="OLD_USER",
        access_token="old_encrypted_token",
        refresh_token="old_encrypted_refresh",
        token_expires_at=get_now() + timedelta(hours=1),
        scope="activity",
        connected_at=get_now()
    )
    test_db.add(existing)
    test_db.commit()

    mock_response = AsyncMock()
    mock_response.json.return_value = {
        "access_token": "new_access_token",
        "refresh_token": "new_refresh_token",
        "user_id": "FITBIT456",
        "scope": "activity heartrate sleep profile",
        "expires_in": 28800
    }
    mock_response.raise_for_status = AsyncMock()

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

        connection = await fitbit_oauth.exchange_code_for_tokens(
            test_db,
            code="test_code",
            profile_id=1
        )

    # Should update existing, not create new
    assert test_db.query(FitbitConnection).count() == 1
    assert connection.fitbit_user_id == "FITBIT456"
    assert connection.scope == "activity heartrate sleep profile"


@pytest.mark.asyncio
async def test_refresh_access_token(test_db: Session, sample_profiles):
    """Test refreshing an expired access token."""
    from app.core.encryption import encrypt_token

    # Create connection with expired token
    connection = FitbitConnection(
        user_id=1,
        fitbit_user_id="FITBIT123",
        access_token=encrypt_token("old_access_token"),
        refresh_token=encrypt_token("old_refresh_token"),
        token_expires_at=get_now() - timedelta(hours=1),  # Expired
        scope="activity",
        connected_at=get_now()
    )
    test_db.add(connection)
    test_db.commit()

    mock_response = AsyncMock()
    mock_response.json.return_value = {
        "access_token": "new_access_token",
        "refresh_token": "new_refresh_token",
        "expires_in": 28800
    }
    mock_response.raise_for_status = AsyncMock()

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

        refreshed = await fitbit_oauth.refresh_access_token(test_db, connection)

    # Verify token was refreshed
    assert refreshed.token_expires_at > get_now()
    # Tokens should be different (encrypted)
    from app.core.encryption import decrypt_token
    assert decrypt_token(refreshed.access_token) == "new_access_token"
    assert decrypt_token(refreshed.refresh_token) == "new_refresh_token"


def test_is_token_expired():
    """Test token expiration check."""
    # Token expired 1 hour ago
    expired_connection = FitbitConnection(
        user_id=1,
        fitbit_user_id="TEST",
        access_token="encrypted",
        refresh_token="encrypted",
        token_expires_at=get_now() - timedelta(hours=1),
        scope="activity",
        connected_at=get_now()
    )
    assert fitbit_oauth.is_token_expired(expired_connection) is True

    # Token expires in 10 minutes (within 5-minute buffer)
    soon_expired_connection = FitbitConnection(
        user_id=1,
        fitbit_user_id="TEST",
        access_token="encrypted",
        refresh_token="encrypted",
        token_expires_at=get_now() + timedelta(minutes=3),
        scope="activity",
        connected_at=get_now()
    )
    assert fitbit_oauth.is_token_expired(soon_expired_connection) is True

    # Token expires in 1 hour (valid)
    valid_connection = FitbitConnection(
        user_id=1,
        fitbit_user_id="TEST",
        access_token="encrypted",
        refresh_token="encrypted",
        token_expires_at=get_now() + timedelta(hours=1),
        scope="activity",
        connected_at=get_now()
    )
    assert fitbit_oauth.is_token_expired(valid_connection) is False


@pytest.mark.asyncio
async def test_ensure_valid_token_refreshes_if_expired(test_db: Session, sample_profiles):
    """Test that ensure_valid_token refreshes expired tokens."""
    from app.core.encryption import encrypt_token

    # Create connection with expired token
    connection = FitbitConnection(
        user_id=1,
        fitbit_user_id="FITBIT123",
        access_token=encrypt_token("old_token"),
        refresh_token=encrypt_token("refresh_token"),
        token_expires_at=get_now() - timedelta(hours=1),
        scope="activity",
        connected_at=get_now()
    )
    test_db.add(connection)
    test_db.commit()

    mock_response = AsyncMock()
    mock_response.json.return_value = {
        "access_token": "new_access_token",
        "refresh_token": "new_refresh_token",
        "expires_in": 28800
    }
    mock_response.raise_for_status = AsyncMock()

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

        result = await fitbit_oauth.ensure_valid_token(test_db, connection)

    assert result.token_expires_at > get_now()


@pytest.mark.asyncio
async def test_ensure_valid_token_does_not_refresh_valid_token(test_db: Session, sample_profiles):
    """Test that ensure_valid_token doesn't refresh valid tokens."""
    from app.core.encryption import encrypt_token

    connection = FitbitConnection(
        user_id=1,
        fitbit_user_id="FITBIT123",
        access_token=encrypt_token("valid_token"),
        refresh_token=encrypt_token("refresh_token"),
        token_expires_at=get_now() + timedelta(hours=2),
        scope="activity",
        connected_at=get_now()
    )
    test_db.add(connection)
    test_db.commit()

    original_expires_at = connection.token_expires_at

    # Should not make any HTTP requests
    result = await fitbit_oauth.ensure_valid_token(test_db, connection)

    assert result.token_expires_at == original_expires_at


@pytest.mark.asyncio
async def test_revoke_token_best_effort(test_db: Session, sample_profiles):
    """Test that token revocation is best-effort and doesn't raise errors."""
    from app.core.encryption import encrypt_token

    connection = FitbitConnection(
        user_id=1,
        fitbit_user_id="FITBIT123",
        access_token=encrypt_token("token_to_revoke"),
        refresh_token=encrypt_token("refresh_token"),
        token_expires_at=get_now() + timedelta(hours=1),
        scope="activity",
        connected_at=get_now()
    )

    # Should not raise even if HTTP request fails
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(side_effect=Exception("Network error"))

        # Should not raise
        await fitbit_oauth.revoke_token(connection)
