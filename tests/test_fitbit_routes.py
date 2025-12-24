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
    assert data["metrics"]["steps"] == 10543
    assert data["metrics"]["sleep_minutes"] == 450
    assert data["metrics"]["active_minutes"] == 35


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
        assert "synced" in data["message"].lower()


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
