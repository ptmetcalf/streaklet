"""Tests for Fitbit scheduler service."""
import pytest
from unittest.mock import patch, MagicMock

from app.services import fitbit_scheduler


@pytest.mark.asyncio
async def test_sync_all_profiles_job_success():
    """Test successful sync job execution."""
    mock_db = MagicMock()
    mock_results = {
        1: {"success_days": 2, "error_days": 0, "total_metrics": 10},
        2: {"success_days": 2, "error_days": 0, "total_metrics": 8}
    }

    with patch("app.services.fitbit_scheduler.get_db") as mock_get_db:
        mock_get_db.return_value = iter([mock_db])

        with patch("app.services.fitbit_scheduler.sync_all_connected_profiles", return_value=mock_results) as mock_sync:
            await fitbit_scheduler.sync_all_profiles_job()

            mock_sync.assert_called_once_with(mock_db)
            mock_db.close.assert_called_once()


@pytest.mark.asyncio
async def test_sync_all_profiles_job_with_errors():
    """Test sync job with some profile errors."""
    mock_db = MagicMock()
    mock_results = {
        1: {"success_days": 2, "error_days": 0, "total_metrics": 10},
        2: {"error": "API Error", "success_days": 0, "error_days": 2, "total_metrics": 0}
    }

    with patch("app.services.fitbit_scheduler.get_db") as mock_get_db:
        mock_get_db.return_value = iter([mock_db])

        with patch("app.services.fitbit_scheduler.sync_all_connected_profiles", return_value=mock_results):
            await fitbit_scheduler.sync_all_profiles_job()

            mock_db.close.assert_called_once()


@pytest.mark.asyncio
async def test_sync_all_profiles_job_exception():
    """Test sync job handles exceptions gracefully."""
    mock_db = MagicMock()

    with patch("app.services.fitbit_scheduler.get_db") as mock_get_db:
        mock_get_db.return_value = iter([mock_db])

        with patch("app.services.fitbit_scheduler.sync_all_connected_profiles", side_effect=Exception("Database error")):
            # Should not raise, just log error
            await fitbit_scheduler.sync_all_profiles_job()

            # Job completes without raising (exception is logged)


def test_start_scheduler():
    """Test starting the scheduler."""
    with patch.object(fitbit_scheduler.scheduler, 'add_job') as mock_add_job:
        with patch.object(fitbit_scheduler.scheduler, 'start') as mock_start:
            fitbit_scheduler.start_scheduler()

            assert mock_add_job.call_count == 2
            mock_start.assert_called_once()

            # Verify Fitbit sync job configuration
            fitbit_call = mock_add_job.call_args_list[0]
            assert fitbit_call[1]['id'] == 'fitbit_sync'
            assert fitbit_call[1]['replace_existing'] is True
            assert fitbit_call[1]['max_instances'] == 1

            # Verify punch list archive job configuration
            archive_call = mock_add_job.call_args_list[1]
            assert archive_call[1]['id'] == 'punch_list_archive'
            assert archive_call[1]['replace_existing'] is True
            assert archive_call[1]['max_instances'] == 1


def test_shutdown_scheduler_running():
    """Test shutting down running scheduler."""
    # Create a mock scheduler with running=True
    mock_scheduler = MagicMock()
    mock_scheduler.running = True

    with patch("app.services.fitbit_scheduler.scheduler", mock_scheduler):
        fitbit_scheduler.shutdown_scheduler()

        mock_scheduler.shutdown.assert_called_once_with(wait=True)


def test_shutdown_scheduler_not_running():
    """Test shutting down when scheduler is not running."""
    # Mock the scheduler to have running=False
    mock_scheduler = MagicMock()
    mock_scheduler.running = False

    with patch("app.services.fitbit_scheduler.scheduler", mock_scheduler):
        fitbit_scheduler.shutdown_scheduler()

        # Should not call shutdown if not running
        mock_scheduler.shutdown.assert_not_called()
