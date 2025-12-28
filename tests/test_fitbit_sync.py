"""Tests for Fitbit sync service."""
import pytest
from datetime import date, timedelta
from unittest.mock import AsyncMock, patch
from sqlalchemy.orm import Session

from app.models.fitbit_connection import FitbitConnection
from app.models.fitbit_metric import FitbitMetric
from app.core.encryption import encrypt_token
from app.core.time import get_now, get_today
from app.services import fitbit_sync


@pytest.mark.asyncio
async def test_upsert_metrics_creates_new(test_db: Session, sample_profiles):
    """Test upserting metrics creates new records."""
    target_date = date(2025, 1, 15)
    metrics = {
        "steps": {"value": 10543, "unit": "steps"},
        "sleep_minutes": {"value": 450, "unit": "minutes"}
    }

    count = await fitbit_sync.upsert_metrics(test_db, profile_id=1, target_date=target_date, metrics=metrics)

    assert count == 2

    # Verify metrics were created
    db_metrics = test_db.query(FitbitMetric).filter(
        FitbitMetric.user_id == 1,
        FitbitMetric.date == target_date
    ).all()

    assert len(db_metrics) == 2
    assert any(m.metric_type == "steps" and m.value == 10543 for m in db_metrics)
    assert any(m.metric_type == "sleep_minutes" and m.value == 450 for m in db_metrics)


@pytest.mark.asyncio
async def test_upsert_metrics_updates_existing(test_db: Session, sample_profiles):
    """Test upserting metrics updates existing records."""
    target_date = date(2025, 1, 15)

    # Create existing metric
    existing = FitbitMetric(
        user_id=1,
        date=target_date,
        metric_type="steps",
        value=5000,
        unit="steps"
    )
    test_db.add(existing)
    test_db.commit()

    # Upsert with new value
    metrics = {
        "steps": {"value": 10543, "unit": "steps"}
    }

    count = await fitbit_sync.upsert_metrics(test_db, profile_id=1, target_date=target_date, metrics=metrics)

    assert count == 1

    # Verify metric was updated
    db_metric = test_db.query(FitbitMetric).filter(
        FitbitMetric.user_id == 1,
        FitbitMetric.date == target_date,
        FitbitMetric.metric_type == "steps"
    ).one()

    assert db_metric.value == 10543


@pytest.mark.asyncio
async def test_sync_profile_date_range_no_connection(test_db: Session, sample_profiles):
    """Test syncing when profile has no connection."""
    start_date = date(2025, 1, 10)
    end_date = date(2025, 1, 12)

    result = await fitbit_sync.sync_profile_date_range(test_db, profile_id=1, start_date=start_date, end_date=end_date)

    assert result["success_days"] == 0
    assert result["error_days"] == 0
    assert result["total_metrics"] == 0
    assert "error" in result


@pytest.mark.asyncio
async def test_sync_profile_date_range_success(test_db: Session, sample_profiles):
    """Test successful date range sync."""
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

    start_date = date(2025, 1, 10)
    end_date = date(2025, 1, 12)

    # Mock fetch_all_metrics
    with patch("app.services.fitbit_api.fetch_all_metrics") as mock_fetch:
        mock_fetch.return_value = {
            "steps": {"value": 10000, "unit": "steps"}
        }

        result = await fitbit_sync.sync_profile_date_range(test_db, profile_id=1, start_date=start_date, end_date=end_date)

        assert result["success_days"] == 3
        assert result["error_days"] == 0
        assert result["total_metrics"] == 3

        # Verify connection status was updated
        test_db.refresh(connection)
        assert connection.last_sync_at is not None
        assert connection.last_sync_status == "success"


@pytest.mark.asyncio
async def test_sync_profile_date_range_partial_failure(test_db: Session, sample_profiles):
    """Test date range sync with some failures."""
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

    start_date = date(2025, 1, 10)
    end_date = date(2025, 1, 12)

    # Mock fetch to fail on some dates
    call_count = 0

    async def mock_fetch_side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            raise Exception("API error")
        return {"steps": {"value": 10000, "unit": "steps"}}

    with patch("app.services.fitbit_api.fetch_all_metrics", side_effect=mock_fetch_side_effect):
        result = await fitbit_sync.sync_profile_date_range(test_db, profile_id=1, start_date=start_date, end_date=end_date)

        assert result["success_days"] == 2
        assert result["error_days"] == 1
        assert result["total_metrics"] == 2

        # Verify connection status shows partial
        test_db.refresh(connection)
        assert connection.last_sync_status == "partial"


@pytest.mark.asyncio
async def test_sync_profile_date_range_no_data(test_db: Session, sample_profiles):
    """Test syncing when no data is available."""
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

    start_date = date(2025, 1, 10)
    end_date = date(2025, 1, 12)

    # Mock fetch to return None (no data)
    with patch("app.services.fitbit_api.fetch_all_metrics") as mock_fetch:
        mock_fetch.return_value = None

        result = await fitbit_sync.sync_profile_date_range(test_db, profile_id=1, start_date=start_date, end_date=end_date)

        assert result["success_days"] == 0
        assert result["error_days"] == 3
        assert result["total_metrics"] == 0


@pytest.mark.asyncio
async def test_sync_profile_recent(test_db: Session, sample_profiles):
    """Test syncing recent data (today + yesterday)."""
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

    # Mock fetch_all_metrics
    with patch("app.services.fitbit_api.fetch_all_metrics") as mock_fetch:
        mock_fetch.return_value = {"steps": {"value": 10000, "unit": "steps"}}

        result = await fitbit_sync.sync_profile_recent(test_db, profile_id=1)

        assert result["success_days"] == 2  # Today + yesterday
        assert result["error_days"] == 0
        assert result["total_metrics"] == 2


@pytest.mark.asyncio
async def test_sync_profile_historical(test_db: Session, sample_profiles):
    """Test syncing historical data."""
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

    # Mock fetch_all_metrics
    with patch("app.services.fitbit_api.fetch_all_metrics") as mock_fetch:
        mock_fetch.return_value = {"steps": {"value": 10000, "unit": "steps"}}

        result = await fitbit_sync.sync_profile_historical(test_db, profile_id=1, days=7)

        assert result["success_days"] == 7
        assert result["error_days"] == 0
        assert result["total_metrics"] == 7


@pytest.mark.asyncio
async def test_sync_all_connected_profiles(test_db: Session, sample_profiles):
    """Test syncing all connected profiles."""
    # Create connections for two profiles
    connection1 = FitbitConnection(
        user_id=1,
        fitbit_user_id="FITBIT1",
        access_token=encrypt_token("token1"),
        refresh_token=encrypt_token("refresh1"),
        token_expires_at=get_now() + timedelta(hours=1),
        scope="activity",
        connected_at=get_now(),
        last_sync_at=get_now()
    )
    connection2 = FitbitConnection(
        user_id=2,
        fitbit_user_id="FITBIT2",
        access_token=encrypt_token("token2"),
        refresh_token=encrypt_token("refresh2"),
        token_expires_at=get_now() + timedelta(hours=1),
        scope="activity",
        connected_at=get_now(),
        last_sync_at=get_now()
    )
    test_db.add(connection1)
    test_db.add(connection2)
    test_db.commit()

    # Mock fetch_all_metrics
    with patch("app.services.fitbit_api.fetch_all_metrics") as mock_fetch:
        mock_fetch.return_value = {"steps": {"value": 10000, "unit": "steps"}}

        results = await fitbit_sync.sync_all_connected_profiles(test_db)

        assert len(results) == 2
        assert 1 in results
        assert 2 in results
        assert results[1]["success_days"] == 2
        assert results[2]["success_days"] == 2


@pytest.mark.asyncio
async def test_sync_all_connected_profiles_with_failure(test_db: Session, sample_profiles):
    """Test syncing all profiles when one fails."""
    # Create connections for two profiles
    connection1 = FitbitConnection(
        user_id=1,
        fitbit_user_id="FITBIT1",
        access_token=encrypt_token("token1"),
        refresh_token=encrypt_token("refresh1"),
        token_expires_at=get_now() + timedelta(hours=1),
        scope="activity",
        connected_at=get_now(),
        last_sync_at=get_now()
    )
    connection2 = FitbitConnection(
        user_id=2,
        fitbit_user_id="FITBIT2",
        access_token=encrypt_token("token2"),
        refresh_token=encrypt_token("refresh2"),
        token_expires_at=get_now() + timedelta(hours=1),
        scope="activity",
        connected_at=get_now(),
        last_sync_at=get_now()
    )
    test_db.add(connection1)
    test_db.add(connection2)
    test_db.commit()

    # Mock sync_profile_smart to fail for profile 1 at top level
    async def mock_sync_side_effect(db, profile_id, backfill_days=7):
        if profile_id == 1:
            raise Exception("API error for profile 1")
        return {"success_days": 2, "error_days": 0, "total_metrics": 2}

    with patch("app.services.fitbit_sync.sync_profile_smart", side_effect=mock_sync_side_effect):
        results = await fitbit_sync.sync_all_connected_profiles(test_db)

        assert len(results) == 2
        assert "error" in results[1]
        assert results[1]["success_days"] == 0
        assert results[2]["success_days"] == 2

        # Verify connection1 status shows error
        test_db.refresh(connection1)
        assert connection1.last_sync_status == "error"
