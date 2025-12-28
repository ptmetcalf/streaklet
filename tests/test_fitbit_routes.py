"""Tests for Fitbit API routes."""
import pytest
from datetime import datetime, timedelta, date
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app.models.fitbit_connection import FitbitConnection
from app.models.fitbit_metric import FitbitMetric
from app.core.encryption import encrypt_token
from app.core.time import get_now


def test_get_fitbit_connect_generates_auth_url(client: TestClient, sample_profiles):
    """Test that /api/fitbit/connect returns an authorization URL."""
    response = client.get("/api/fitbit/connect")

    assert response.status_code == 200
    data = response.json()
    assert "redirect_url" in data
    assert "https://www.fitbit.com/oauth2/authorize" in data["redirect_url"]
    assert "client_id=" in data["redirect_url"]
    assert "state=" in data["redirect_url"]


def test_get_fitbit_connection_status_not_connected(client: TestClient, sample_profiles):
    """Test connection status when not connected."""
    response = client.get("/api/fitbit/connection")

    assert response.status_code == 200
    data = response.json()
    assert data["connected"] is False
    assert data["fitbit_user_id"] is None
    assert data["last_sync_at"] is None


def test_get_fitbit_connection_status_connected(client: TestClient, test_db, sample_profiles):
    """Test connection status when connected."""
    # Create connection
    connection = FitbitConnection(
        user_id=1,
        fitbit_user_id="FITBIT123",
        access_token=encrypt_token("access_token"),
        refresh_token=encrypt_token("refresh_token"),
        token_expires_at=get_now() + timedelta(hours=1),
        scope="activity heartrate",
        connected_at=get_now(),
        last_sync_at=get_now(),
        last_sync_status="success"
    )
    test_db.add(connection)
    test_db.commit()

    response = client.get("/api/fitbit/connection")

    assert response.status_code == 200
    data = response.json()
    assert data["connected"] is True
    assert data["fitbit_user_id"] == "FITBIT123"
    assert data["last_sync_status"] == "success"


def test_delete_fitbit_connection(client: TestClient, test_db, sample_profiles):
    """Test disconnecting Fitbit account."""
    # Create connection
    connection = FitbitConnection(
        user_id=1,
        fitbit_user_id="FITBIT123",
        access_token=encrypt_token("access_token"),
        refresh_token=encrypt_token("refresh_token"),
        token_expires_at=get_now() + timedelta(hours=1),
        scope="activity",
        connected_at=get_now()
    )
    test_db.add(connection)
    test_db.commit()

    response = client.delete("/api/fitbit/connection")

    assert response.status_code == 204

    # Verify connection is deleted
    from app.services import fitbit_connection
    assert fitbit_connection.get_connection(test_db, profile_id=1) is None


def test_delete_fitbit_connection_not_exists(client: TestClient, sample_profiles):
    """Test deleting connection that doesn't exist."""
    response = client.delete("/api/fitbit/connection")

    # Should succeed (idempotent)
    assert response.status_code == 204


def test_get_fitbit_metrics_no_connection(client: TestClient, sample_profiles):
    """Test getting metrics when not connected returns 404."""
    response = client.get("/api/fitbit/metrics?start_date=2025-01-01&end_date=2025-01-10")

    assert response.status_code == 404
    assert "not connected" in response.json()["detail"].lower()


def test_get_fitbit_metrics(client: TestClient, test_db, sample_profiles):
    """Test retrieving Fitbit metrics."""
    # Create connection
    connection = FitbitConnection(
        user_id=1,
        fitbit_user_id="FITBIT123",
        access_token=encrypt_token("access_token"),
        refresh_token=encrypt_token("refresh_token"),
        token_expires_at=get_now() + timedelta(hours=1),
        scope="activity",
        connected_at=get_now()
    )
    test_db.add(connection)
    test_db.commit()

    # Create metrics
    metric1 = FitbitMetric(
        user_id=1,
        date=date(2025, 1, 15),
        metric_type="steps",
        value=10543,
        unit="steps"
    )
    metric2 = FitbitMetric(
        user_id=1,
        date=date(2025, 1, 15),
        metric_type="sleep_minutes",
        value=450,
        unit="minutes"
    )
    test_db.add(metric1)
    test_db.add(metric2)
    test_db.commit()

    response = client.get("/api/fitbit/metrics?start_date=2025-01-15&end_date=2025-01-15")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert any(m["metric_type"] == "steps" and m["value"] == 10543 for m in data)
    assert any(m["metric_type"] == "sleep_minutes" and m["value"] == 450 for m in data)


def test_get_fitbit_metrics_filters_by_date(client: TestClient, test_db, sample_profiles):
    """Test that metrics are filtered by date range."""
    # Create connection
    connection = FitbitConnection(
        user_id=1,
        fitbit_user_id="FITBIT123",
        access_token=encrypt_token("access_token"),
        refresh_token=encrypt_token("refresh_token"),
        token_expires_at=get_now() + timedelta(hours=1),
        scope="activity",
        connected_at=get_now()
    )
    test_db.add(connection)
    test_db.commit()

    # Create metrics for different dates
    metric1 = FitbitMetric(
        user_id=1,
        date=date(2025, 1, 10),
        metric_type="steps",
        value=8000,
        unit="steps"
    )
    metric2 = FitbitMetric(
        user_id=1,
        date=date(2025, 1, 15),
        metric_type="steps",
        value=10000,
        unit="steps"
    )
    metric3 = FitbitMetric(
        user_id=1,
        date=date(2025, 1, 20),
        metric_type="steps",
        value=12000,
        unit="steps"
    )
    test_db.add_all([metric1, metric2, metric3])
    test_db.commit()

    # Query for Jan 15 only
    response = client.get("/api/fitbit/metrics?start_date=2025-01-15&end_date=2025-01-15")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["value"] == 10000


def test_get_fitbit_daily_summary(client: TestClient, test_db, sample_profiles):
    """Test getting daily summary of all metrics."""
    # Create connection
    connection = FitbitConnection(
        user_id=1,
        fitbit_user_id="FITBIT123",
        access_token=encrypt_token("access_token"),
        refresh_token=encrypt_token("refresh_token"),
        token_expires_at=get_now() + timedelta(hours=1),
        scope="activity",
        connected_at=get_now()
    )
    test_db.add(connection)
    test_db.commit()

    # Create multiple metrics for the same day
    metrics = [
        FitbitMetric(user_id=1, date=date(2025, 1, 15), metric_type="steps", value=10543, unit="steps"),
        FitbitMetric(user_id=1, date=date(2025, 1, 15), metric_type="sleep_minutes", value=450, unit="minutes"),
        FitbitMetric(user_id=1, date=date(2025, 1, 15), metric_type="active_minutes", value=35, unit="minutes"),
    ]
    test_db.add_all(metrics)
    test_db.commit()

    response = client.get("/api/fitbit/daily-summary?date=2025-01-15")

    assert response.status_code == 200
    data = response.json()
    assert data["date"] == "2025-01-15"
    assert "metrics" in data
    assert data["metrics"]["steps"]["value"] == 10543
    assert data["metrics"]["steps"]["unit"] == "steps"
    assert data["metrics"]["sleep_minutes"]["value"] == 450
    assert data["metrics"]["sleep_minutes"]["unit"] == "minutes"
    assert data["metrics"]["active_minutes"]["value"] == 35
    assert data["metrics"]["active_minutes"]["unit"] == "minutes"


def test_get_fitbit_daily_summary_no_data(client: TestClient, test_db, sample_profiles):
    """Test daily summary when no data exists."""
    # Create connection
    connection = FitbitConnection(
        user_id=1,
        fitbit_user_id="FITBIT123",
        access_token=encrypt_token("access_token"),
        refresh_token=encrypt_token("refresh_token"),
        token_expires_at=get_now() + timedelta(hours=1),
        scope="activity",
        connected_at=get_now()
    )
    test_db.add(connection)
    test_db.commit()

    response = client.get("/api/fitbit/daily-summary?date=2025-01-15")

    assert response.status_code == 200
    data = response.json()
    assert data["date"] == "2025-01-15"
    assert data["metrics"] == {}


def test_post_fitbit_sync_triggers_sync(client: TestClient, test_db, sample_profiles):
    """Test manual sync trigger."""
    # Create connection
    connection = FitbitConnection(
        user_id=1,
        fitbit_user_id="FITBIT123",
        access_token=encrypt_token("access_token"),
        refresh_token=encrypt_token("refresh_token"),
        token_expires_at=get_now() + timedelta(hours=8),
        scope="activity heartrate sleep",
        connected_at=get_now()
    )
    test_db.add(connection)
    test_db.commit()

    # Mock the sync service
    with patch("app.services.fitbit_sync.sync_profile_recent") as mock_sync:
        mock_sync.return_value = {"success": 2, "errors": 0}

        response = client.post("/api/fitbit/sync")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "sync completed" in data["message"].lower()


def test_post_fitbit_sync_not_connected(client: TestClient, sample_profiles):
    """Test manual sync when not connected returns 404."""
    response = client.post("/api/fitbit/sync")

    assert response.status_code == 404
    assert "not connected" in response.json()["detail"].lower()


def test_fitbit_routes_respect_profile_header(client: TestClient, test_db, sample_profiles):
    """Test that Fitbit routes respect X-Profile-Id header."""
    # Create connections for two profiles
    connection1 = FitbitConnection(
        user_id=1,
        fitbit_user_id="FITBIT_USER1",
        access_token=encrypt_token("token1"),
        refresh_token=encrypt_token("refresh1"),
        token_expires_at=get_now() + timedelta(hours=1),
        scope="activity",
        connected_at=get_now()
    )
    connection2 = FitbitConnection(
        user_id=2,
        fitbit_user_id="FITBIT_USER2",
        access_token=encrypt_token("token2"),
        refresh_token=encrypt_token("refresh2"),
        token_expires_at=get_now() + timedelta(hours=1),
        scope="activity",
        connected_at=get_now()
    )
    test_db.add(connection1)
    test_db.add(connection2)
    test_db.commit()

    # Request for profile 1
    response1 = client.get("/api/fitbit/connection", headers={"X-Profile-Id": "1"})
    assert response1.status_code == 200
    assert response1.json()["fitbit_user_id"] == "FITBIT_USER1"

    # Request for profile 2
    response2 = client.get("/api/fitbit/connection", headers={"X-Profile-Id": "2"})
    assert response2.status_code == 200
    assert response2.json()["fitbit_user_id"] == "FITBIT_USER2"


def test_oauth_callback_with_error(client: TestClient, sample_profiles):
    """Test OAuth callback when Fitbit returns a known error."""
    response = client.get("/api/fitbit/callback?error=access_denied&state=test_state", follow_redirects=False)

    assert response.status_code == 307
    assert "/settings?fitbit=error&message=access_denied" in response.headers["location"]


def test_oauth_callback_with_unknown_error(client: TestClient, sample_profiles):
    """Test OAuth callback with unknown error gets mapped to oauth_error."""
    # Try to inject an unknown/malicious error code
    response = client.get("/api/fitbit/callback?error=malicious_code&state=test_state", follow_redirects=False)

    assert response.status_code == 307
    location = response.headers["location"]

    # Unknown error should be mapped to generic "oauth_error"
    assert "/settings?fitbit=error&message=oauth_error" in location
    assert "malicious_code" not in location


def test_oauth_callback_missing_code(client: TestClient, sample_profiles):
    """Test OAuth callback with missing code parameter."""
    response = client.get("/api/fitbit/callback?state=test_state", follow_redirects=False)

    assert response.status_code == 307
    assert "/settings?fitbit=error&message=missing_parameters" in response.headers["location"]


def test_oauth_callback_missing_state(client: TestClient, sample_profiles):
    """Test OAuth callback with missing state parameter."""
    response = client.get("/api/fitbit/callback?code=test_code", follow_redirects=False)

    assert response.status_code == 307
    assert "/settings?fitbit=error&message=missing_parameters" in response.headers["location"]


def test_oauth_callback_invalid_state(client: TestClient, sample_profiles):
    """Test OAuth callback with invalid state token."""
    response = client.get("/api/fitbit/callback?code=test_code&state=invalid_state", follow_redirects=False)

    assert response.status_code == 307
    assert "/settings?fitbit=error&message=invalid_state" in response.headers["location"]


def test_oauth_callback_success(client: TestClient, sample_profiles):
    """Test successful OAuth callback flow."""
    # First, initiate connection to get valid state
    init_response = client.get("/api/fitbit/connect")
    state = init_response.json()["state"]

    # Mock successful token exchange
    with patch("app.services.fitbit_oauth.exchange_code_for_tokens") as mock_exchange:
        mock_exchange.return_value = None

        response = client.get(f"/api/fitbit/callback?code=test_auth_code&state={state}", follow_redirects=False)

        assert response.status_code == 307
        assert response.headers["location"] == "/settings?fitbit=connected"


def test_oauth_callback_exchange_failure(client: TestClient, sample_profiles):
    """Test OAuth callback when token exchange fails."""
    # First, initiate connection to get valid state
    init_response = client.get("/api/fitbit/connect")
    state = init_response.json()["state"]

    # Mock token exchange to raise exception
    with patch("app.services.fitbit_oauth.exchange_code_for_tokens") as mock_exchange:
        mock_exchange.side_effect = Exception("Token exchange failed")

        response = client.get(f"/api/fitbit/callback?code=test_code&state={state}", follow_redirects=False)

        assert response.status_code == 307
        location = response.headers["location"]
        assert "/settings?fitbit=error&message=" in location
        # URL-encoded version of "Token exchange failed"
        assert "Token" in location and "exchange" in location and "failed" in location


def test_manual_sync_failure(client: TestClient, test_db, sample_profiles):
    """Test manual sync when sync service fails."""
    # Create connection
    connection = FitbitConnection(
        user_id=1,
        fitbit_user_id="FITBIT123",
        access_token=encrypt_token("access_token"),
        refresh_token=encrypt_token("refresh_token"),
        token_expires_at=get_now() + timedelta(hours=8),
        scope="activity heartrate sleep",
        connected_at=get_now()
    )
    test_db.add(connection)
    test_db.commit()

    # Mock sync to fail
    with patch("app.services.fitbit_sync.sync_profile_smart") as mock_sync:
        mock_sync.side_effect = Exception("Sync service failed")

        response = client.post("/api/fitbit/sync")

        assert response.status_code == 500
        assert "Sync failed" in response.json()["detail"]
        assert "Sync service failed" in response.json()["detail"]


def test_get_sync_status_not_connected(client: TestClient, sample_profiles):
    """Test getting sync status when not connected returns 404."""
    response = client.get("/api/fitbit/sync-status")

    assert response.status_code == 404
    assert "not connected" in response.json()["detail"].lower()


def test_get_sync_status_success(client: TestClient, test_db, sample_profiles):
    """Test getting sync status when connected."""
    connection = FitbitConnection(
        user_id=1,
        fitbit_user_id="FITBIT123",
        access_token=encrypt_token("access_token"),
        refresh_token=encrypt_token("refresh_token"),
        token_expires_at=get_now() + timedelta(hours=1),
        scope="activity",
        connected_at=get_now(),
        last_sync_at=get_now(),
        last_sync_status="success"
    )
    test_db.add(connection)
    test_db.commit()

    response = client.get("/api/fitbit/sync-status")

    assert response.status_code == 200
    data = response.json()
    assert data["is_syncing"] is False
    assert data["last_sync_status"] == "success"
    assert data["last_sync_at"] is not None


def test_get_metrics_with_type_filter(client: TestClient, test_db, sample_profiles):
    """Test retrieving metrics filtered by type."""
    # Create connection
    connection = FitbitConnection(
        user_id=1,
        fitbit_user_id="FITBIT123",
        access_token=encrypt_token("access_token"),
        refresh_token=encrypt_token("refresh_token"),
        token_expires_at=get_now() + timedelta(hours=1),
        scope="activity",
        connected_at=get_now()
    )
    test_db.add(connection)
    test_db.commit()

    # Create multiple metric types
    metrics = [
        FitbitMetric(user_id=1, date=date(2025, 1, 15), metric_type="steps", value=10543, unit="steps"),
        FitbitMetric(user_id=1, date=date(2025, 1, 15), metric_type="sleep_minutes", value=450, unit="minutes"),
        FitbitMetric(user_id=1, date=date(2025, 1, 15), metric_type="active_minutes", value=35, unit="minutes"),
    ]
    test_db.add_all(metrics)
    test_db.commit()

    # Filter for only steps and sleep
    response = client.get("/api/fitbit/metrics?start_date=2025-01-15&end_date=2025-01-15&metric_types=steps,sleep_minutes")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert any(m["metric_type"] == "steps" for m in data)
    assert any(m["metric_type"] == "sleep_minutes" for m in data)
    assert not any(m["metric_type"] == "active_minutes" for m in data)


def test_get_daily_summary_not_connected(client: TestClient, sample_profiles):
    """Test getting daily summary when not connected returns 404."""
    response = client.get("/api/fitbit/daily-summary?date=2025-01-15")

    assert response.status_code == 404
    assert "not connected" in response.json()["detail"].lower()


def test_get_metrics_history(client: TestClient, test_db, sample_profiles):
    """Test getting historical metrics data."""
    # Create connection
    connection = FitbitConnection(
        user_id=1,
        fitbit_user_id="FITBIT123",
        access_token=encrypt_token("access_token"),
        refresh_token=encrypt_token("refresh_token"),
        token_expires_at=get_now() + timedelta(hours=1),
        scope="activity",
        connected_at=get_now()
    )
    test_db.add(connection)
    test_db.commit()

    # Create metrics for multiple dates
    metrics = [
        FitbitMetric(user_id=1, date=date(2025, 1, 10), metric_type="steps", value=8000, unit="steps"),
        FitbitMetric(user_id=1, date=date(2025, 1, 11), metric_type="steps", value=9000, unit="steps"),
        FitbitMetric(user_id=1, date=date(2025, 1, 12), metric_type="steps", value=10000, unit="steps"),
        FitbitMetric(user_id=1, date=date(2025, 1, 10), metric_type="sleep_minutes", value=420, unit="minutes"),
        FitbitMetric(user_id=1, date=date(2025, 1, 11), metric_type="sleep_minutes", value=450, unit="minutes"),
    ]
    test_db.add_all(metrics)
    test_db.commit()

    response = client.get("/api/fitbit/metrics/history?start_date=2025-01-10&end_date=2025-01-12")

    assert response.status_code == 200
    data = response.json()
    assert data["start_date"] == "2025-01-10"
    assert data["end_date"] == "2025-01-12"
    assert "metrics" in data
    assert "steps" in data["metrics"]
    assert "sleep_minutes" in data["metrics"]
    assert len(data["metrics"]["steps"]) == 3
    assert len(data["metrics"]["sleep_minutes"]) == 2
    assert data["metrics"]["steps"][0]["date"] == "2025-01-10"
    assert data["metrics"]["steps"][0]["value"] == 8000


def test_get_metrics_history_with_type_filter(client: TestClient, test_db, sample_profiles):
    """Test getting historical metrics filtered by type."""
    # Create connection
    connection = FitbitConnection(
        user_id=1,
        fitbit_user_id="FITBIT123",
        access_token=encrypt_token("access_token"),
        refresh_token=encrypt_token("refresh_token"),
        token_expires_at=get_now() + timedelta(hours=1),
        scope="activity",
        connected_at=get_now()
    )
    test_db.add(connection)
    test_db.commit()

    # Create metrics for multiple dates and types
    metrics = [
        FitbitMetric(user_id=1, date=date(2025, 1, 10), metric_type="steps", value=8000, unit="steps"),
        FitbitMetric(user_id=1, date=date(2025, 1, 10), metric_type="sleep_minutes", value=420, unit="minutes"),
        FitbitMetric(user_id=1, date=date(2025, 1, 10), metric_type="active_minutes", value=30, unit="minutes"),
    ]
    test_db.add_all(metrics)
    test_db.commit()

    response = client.get("/api/fitbit/metrics/history?start_date=2025-01-10&end_date=2025-01-10&metric_types=steps")

    assert response.status_code == 200
    data = response.json()
    assert "steps" in data["metrics"]
    assert "sleep_minutes" not in data["metrics"]
    assert "active_minutes" not in data["metrics"]
    assert len(data["metrics"]["steps"]) == 1


def test_get_metrics_history_not_connected(client: TestClient, sample_profiles):
    """Test getting metrics history when not connected returns 404."""
    response = client.get("/api/fitbit/metrics/history?start_date=2025-01-01&end_date=2025-01-10")

    assert response.status_code == 404
    assert "not connected" in response.json()["detail"].lower()


def test_safe_settings_redirect_sanitizes_user_input(client: TestClient, sample_profiles):
    """Test that OAuth callback prevents open redirect by always redirecting to /settings."""
    # Try to inject a malicious URL in the error parameter
    malicious_error = "https://evil.com/phishing"
    response = client.get(f"/api/fitbit/callback?error={malicious_error}&state=invalid", follow_redirects=False)

    assert response.status_code == 307
    location = response.headers["location"]

    # CRITICAL: Should always redirect to /settings (never to external URL)
    # This prevents open redirect vulnerability
    assert location.startswith("/settings")
    assert not location.startswith("https://")
    assert not location.startswith("http://")

    # Error message is URL-encoded in query param (safe - not the redirect target)
    assert "message=" in location


def test_safe_settings_redirect_limits_message_length(client: TestClient, sample_profiles):
    """Test that error messages are truncated to prevent abuse."""
    # Create a very long error message
    long_error = "A" * 500  # 500 characters
    response = client.get(f"/api/fitbit/callback?error={long_error}&state=invalid", follow_redirects=False)

    assert response.status_code == 307
    location = response.headers["location"]

    # Should always redirect to /settings
    assert location.startswith("/settings")

    # Message should be truncated (max 200 chars after encoding)
    # The actual location will be longer due to URL encoding, but original message was truncated
    assert len(location) < 300  # Reasonable limit
