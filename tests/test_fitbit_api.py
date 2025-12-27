"""Tests for Fitbit API service."""
import pytest
from datetime import date, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.orm import Session
import httpx

from app.models.fitbit_connection import FitbitConnection
from app.core.encryption import encrypt_token
from app.core.time import get_now
from app.services import fitbit_api


@pytest.fixture
def mock_connection(test_db: Session, sample_profiles):
    """Create a mock Fitbit connection."""
    connection = FitbitConnection(
        user_id=1,
        fitbit_user_id="FITBIT123",
        access_token=encrypt_token("test_access_token"),
        refresh_token=encrypt_token("test_refresh_token"),
        token_expires_at=get_now() + timedelta(hours=1),
        scope="activity heartrate sleep",
        connected_at=get_now()
    )
    test_db.add(connection)
    test_db.commit()
    test_db.refresh(connection)
    return connection


@pytest.mark.asyncio
async def test_make_fitbit_request_success(test_db: Session, mock_connection):
    """Test successful Fitbit API request."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.is_success = True
    mock_response.json.return_value = {"data": "test"}

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

        result = await fitbit_api._make_fitbit_request(test_db, mock_connection, "/test/endpoint")

        assert result == {"data": "test"}


@pytest.mark.asyncio
async def test_make_fitbit_request_rate_limit(test_db: Session, mock_connection):
    """Test Fitbit API rate limit handling."""
    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_response.is_success = False

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

        with pytest.raises(fitbit_api.FitbitAPIError, match="Rate limit exceeded"):
            await fitbit_api._make_fitbit_request(test_db, mock_connection, "/test/endpoint")


@pytest.mark.asyncio
async def test_make_fitbit_request_error(test_db: Session, mock_connection):
    """Test Fitbit API error handling."""
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.is_success = False
    mock_response.text = "Internal Server Error"

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

        with pytest.raises(fitbit_api.FitbitAPIError, match="Fitbit API error: 500"):
            await fitbit_api._make_fitbit_request(test_db, mock_connection, "/test/endpoint")


@pytest.mark.asyncio
async def test_make_fitbit_request_401_retry(test_db: Session, mock_connection):
    """Test Fitbit API retries on 401."""
    mock_response_401 = MagicMock()
    mock_response_401.status_code = 401
    mock_response_401.is_success = False

    mock_response_200 = MagicMock()
    mock_response_200.status_code = 200
    mock_response_200.is_success = True
    mock_response_200.json.return_value = {"data": "success"}

    with patch("httpx.AsyncClient") as mock_client:
        mock_get = AsyncMock(side_effect=[mock_response_401, mock_response_200])
        mock_client.return_value.__aenter__.return_value.get = mock_get

        with patch("app.services.fitbit_api.ensure_valid_token", return_value=mock_connection):
            result = await fitbit_api._make_fitbit_request(test_db, mock_connection, "/test/endpoint")

            assert result == {"data": "success"}
            assert mock_get.call_count == 2


@pytest.mark.asyncio
async def test_fetch_activity_summary_success(test_db: Session, mock_connection):
    """Test fetching activity summary."""
    mock_data = {
        "summary": {
            "steps": 10543,
            "floors": 12,
            "caloriesOut": 2500,
            "fairlyActiveMinutes": 20,
            "veryActiveMinutes": 35,
            "distances": [
                {"activity": "tracker", "distance": 4.8},  # Tracker distance (preferred)
                {"activity": "total", "distance": 5.2}
            ]
        }
    }

    with patch("app.services.fitbit_api._make_fitbit_request", return_value=mock_data):
        target_date = date(2025, 1, 15)
        metrics = await fitbit_api.fetch_activity_summary(test_db, mock_connection, target_date)

        assert metrics["steps"] == 10543
        assert metrics["floors"] == 12
        assert metrics["calories_burned"] == 2500
        assert metrics["active_minutes_legacy"] == 55  # 20 + 35 (legacy fallback)
        assert metrics["distance"] == 4.8  # Uses "tracker" not "total"


@pytest.mark.asyncio
async def test_fetch_activity_summary_partial_data(test_db: Session, mock_connection):
    """Test fetching activity summary with partial data."""
    mock_data = {
        "summary": {
            "steps": 5000
            # Missing other fields
        }
    }

    with patch("app.services.fitbit_api._make_fitbit_request", return_value=mock_data):
        target_date = date(2025, 1, 15)
        metrics = await fitbit_api.fetch_activity_summary(test_db, mock_connection, target_date)

        assert metrics["steps"] == 5000
        assert "floors" not in metrics
        assert "calories_burned" not in metrics


@pytest.mark.asyncio
async def test_fetch_activity_summary_error(test_db: Session, mock_connection):
    """Test activity summary fetch error."""
    with patch("app.services.fitbit_api._make_fitbit_request", side_effect=Exception("API Error")):
        target_date = date(2025, 1, 15)

        with pytest.raises(fitbit_api.FitbitAPIError, match="Failed to fetch activity summary"):
            await fitbit_api.fetch_activity_summary(test_db, mock_connection, target_date)


@pytest.mark.asyncio
async def test_fetch_sleep_summary_success(test_db: Session, mock_connection):
    """Test fetching sleep summary."""
    mock_data = {
        "sleep": [
            {
                "minutesAsleep": 450,
                "isMainSleep": True,
                "efficiency": 92
            }
        ]
    }

    with patch("app.services.fitbit_api._make_fitbit_request", return_value=mock_data):
        target_date = date(2025, 1, 15)
        metrics = await fitbit_api.fetch_sleep_summary(test_db, mock_connection, target_date)

        assert metrics["sleep_minutes"] == 450
        assert metrics["sleep_score"] == 92


@pytest.mark.asyncio
async def test_fetch_sleep_summary_multiple_records(test_db: Session, mock_connection):
    """Test fetching sleep summary with multiple sleep records."""
    mock_data = {
        "sleep": [
            {"minutesAsleep": 420, "isMainSleep": True, "efficiency": 90},
            {"minutesAsleep": 30, "isMainSleep": False}  # Nap
        ]
    }

    with patch("app.services.fitbit_api._make_fitbit_request", return_value=mock_data):
        target_date = date(2025, 1, 15)
        metrics = await fitbit_api.fetch_sleep_summary(test_db, mock_connection, target_date)

        assert metrics["sleep_minutes"] == 450  # 420 + 30
        assert metrics["sleep_score"] == 90


@pytest.mark.asyncio
async def test_fetch_sleep_summary_no_data(test_db: Session, mock_connection):
    """Test fetching sleep summary with no data."""
    mock_data = {"sleep": []}

    with patch("app.services.fitbit_api._make_fitbit_request", return_value=mock_data):
        target_date = date(2025, 1, 15)
        metrics = await fitbit_api.fetch_sleep_summary(test_db, mock_connection, target_date)

        assert metrics == {}


@pytest.mark.asyncio
async def test_fetch_sleep_summary_error(test_db: Session, mock_connection):
    """Test sleep summary fetch error returns empty dict."""
    with patch("app.services.fitbit_api._make_fitbit_request", side_effect=Exception("API Error")):
        target_date = date(2025, 1, 15)
        metrics = await fitbit_api.fetch_sleep_summary(test_db, mock_connection, target_date)

        # Should return empty dict, not raise
        assert metrics == {}


@pytest.mark.asyncio
async def test_fetch_heart_rate_summary_success(test_db: Session, mock_connection):
    """Test fetching heart rate summary."""
    mock_data = {
        "activities-heart": [
            {
                "value": {
                    "restingHeartRate": 62
                }
            }
        ]
    }

    with patch("app.services.fitbit_api._make_fitbit_request", return_value=mock_data):
        target_date = date(2025, 1, 15)
        metrics = await fitbit_api.fetch_heart_rate_summary(test_db, mock_connection, target_date)

        assert metrics["resting_heart_rate"] == 62


@pytest.mark.asyncio
async def test_fetch_heart_rate_summary_no_data(test_db: Session, mock_connection):
    """Test fetching heart rate with no data."""
    mock_data = {"activities-heart": []}

    with patch("app.services.fitbit_api._make_fitbit_request", return_value=mock_data):
        target_date = date(2025, 1, 15)
        metrics = await fitbit_api.fetch_heart_rate_summary(test_db, mock_connection, target_date)

        assert metrics == {}


@pytest.mark.asyncio
async def test_fetch_heart_rate_summary_error(test_db: Session, mock_connection):
    """Test heart rate fetch error returns empty dict."""
    with patch("app.services.fitbit_api._make_fitbit_request", side_effect=Exception("API Error")):
        target_date = date(2025, 1, 15)
        metrics = await fitbit_api.fetch_heart_rate_summary(test_db, mock_connection, target_date)

        # Should return empty dict, not raise
        assert metrics == {}


@pytest.mark.asyncio
async def test_fetch_all_metrics_success(test_db: Session, mock_connection):
    """Test fetching all metrics combines activity, sleep, and heart rate."""
    async def mock_activity(*args):
        return {"steps": 10000, "calories_burned": 2500}

    async def mock_sleep(*args):
        return {"sleep_minutes": 450}

    async def mock_hr(*args):
        return {"resting_heart_rate": 62}

    with patch("app.services.fitbit_api.fetch_activity_summary", side_effect=mock_activity):
        with patch("app.services.fitbit_api.fetch_sleep_summary", side_effect=mock_sleep):
            with patch("app.services.fitbit_api.fetch_heart_rate_summary", side_effect=mock_hr):
                target_date = date(2025, 1, 15)
                metrics = await fitbit_api.fetch_all_metrics(test_db, mock_connection, target_date)

                assert "steps" in metrics
                assert metrics["steps"]["value"] == 10000
                assert metrics["steps"]["unit"] == "steps"

                assert "calories_burned" in metrics
                assert metrics["calories_burned"]["value"] == 2500
                assert metrics["calories_burned"]["unit"] == "calories"

                assert "sleep_minutes" in metrics
                assert metrics["sleep_minutes"]["value"] == 450
                assert metrics["sleep_minutes"]["unit"] == "minutes"

                assert "resting_heart_rate" in metrics
                assert metrics["resting_heart_rate"]["value"] == 62
                assert metrics["resting_heart_rate"]["unit"] == "bpm"


@pytest.mark.asyncio
async def test_fetch_all_metrics_partial_failure(test_db: Session, mock_connection):
    """Test fetching all metrics when some sources fail."""
    async def mock_activity(*args):
        return {"steps": 10000}

    async def mock_sleep(*args):
        raise Exception("Sleep API unavailable")

    async def mock_hr(*args):
        return {"resting_heart_rate": 62}

    with patch("app.services.fitbit_api.fetch_activity_summary", side_effect=mock_activity):
        with patch("app.services.fitbit_api.fetch_sleep_summary", side_effect=mock_sleep):
            with patch("app.services.fitbit_api.fetch_heart_rate_summary", side_effect=mock_hr):
                target_date = date(2025, 1, 15)
                metrics = await fitbit_api.fetch_all_metrics(test_db, mock_connection, target_date)

                # Should still return activity and heart rate
                assert "steps" in metrics
                assert "resting_heart_rate" in metrics
                # Sleep should be missing
                assert "sleep_minutes" not in metrics


@pytest.mark.asyncio
async def test_fetch_all_metrics_activity_api_error(test_db: Session, mock_connection):
    """Test fetching all metrics when activity API raises FitbitAPIError."""
    async def mock_activity(*args):
        raise fitbit_api.FitbitAPIError("Activity API failed")

    async def mock_sleep(*args):
        return {"sleep_minutes": 450}

    async def mock_hr(*args):
        return {}

    with patch("app.services.fitbit_api.fetch_activity_summary", side_effect=mock_activity):
        with patch("app.services.fitbit_api.fetch_sleep_summary", side_effect=mock_sleep):
            with patch("app.services.fitbit_api.fetch_heart_rate_summary", side_effect=mock_hr):
                target_date = date(2025, 1, 15)
                metrics = await fitbit_api.fetch_all_metrics(test_db, mock_connection, target_date)

                # Should still return sleep data
                assert "sleep_minutes" in metrics
                # Activity should be missing
                assert "steps" not in metrics
