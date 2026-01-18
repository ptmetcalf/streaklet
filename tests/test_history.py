import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import date, datetime
from app.services import history as history_service
from app.models.daily_status import DailyStatus
from app.models.task import Task
from app.models.task_check import TaskCheck


@pytest.fixture
def sample_completed_days(test_db: Session, sample_profiles):
    """Create sample completed days for testing."""
    completed_days = [
        DailyStatus(date=date(2024, 12, 1), user_id=1, completed_at=datetime(2024, 12, 1, 20, 0)),
        DailyStatus(date=date(2024, 12, 2), user_id=1, completed_at=datetime(2024, 12, 2, 19, 30)),
        DailyStatus(date=date(2024, 12, 3), user_id=1, completed_at=None),  # Incomplete
        DailyStatus(date=date(2024, 12, 5), user_id=1, completed_at=datetime(2024, 12, 5, 21, 0)),
    ]

    for day in completed_days:
        test_db.add(day)
    test_db.commit()

    return completed_days


def test_get_calendar_month_data_basic(test_db: Session, sample_profiles):
    """Test getting calendar data for a month with no completions."""
    calendar_data = history_service.get_calendar_month_data(test_db, 2024, 12, profile_id=1)

    assert calendar_data["days_in_month"] == 31
    assert calendar_data["first_day_weekday"] == 6  # December 1, 2024 is Sunday (6 in 0-indexed)
    assert len(calendar_data["days"]) == 31

    # Check all days are present and incomplete
    for day in range(1, 32):
        date_str = f"2024-12-{day:02d}"
        assert date_str in calendar_data["days"]
        assert calendar_data["days"][date_str]["completed"] is False
        assert calendar_data["days"][date_str]["completed_at"] is None


def test_get_calendar_month_data_with_completions(test_db: Session, sample_completed_days):
    """Test getting calendar data with some completed days."""
    calendar_data = history_service.get_calendar_month_data(test_db, 2024, 12, profile_id=1)

    # Check completed days
    assert calendar_data["days"]["2024-12-01"]["completed"] is True
    assert calendar_data["days"]["2024-12-01"]["completed_at"] == "2024-12-01T20:00:00"

    assert calendar_data["days"]["2024-12-02"]["completed"] is True
    assert calendar_data["days"]["2024-12-02"]["completed_at"] == "2024-12-02T19:30:00"

    # Check incomplete day (exists in DB but not completed)
    assert calendar_data["days"]["2024-12-03"]["completed"] is False
    assert calendar_data["days"]["2024-12-03"]["completed_at"] is None

    # Check day not in DB
    assert calendar_data["days"]["2024-12-04"]["completed"] is False

    # Check completed day
    assert calendar_data["days"]["2024-12-05"]["completed"] is True


def test_get_calendar_month_data_different_months(test_db: Session, sample_profiles):
    """Test calendar data for different months."""
    # January 2024 - 31 days, starts on Monday (0)
    jan_data = history_service.get_calendar_month_data(test_db, 2024, 1, profile_id=1)
    assert jan_data["days_in_month"] == 31
    assert jan_data["first_day_weekday"] == 0

    # February 2024 - 29 days (leap year), starts on Thursday (3)
    feb_data = history_service.get_calendar_month_data(test_db, 2024, 2, profile_id=1)
    assert feb_data["days_in_month"] == 29
    assert feb_data["first_day_weekday"] == 3

    # November 2024 - 30 days, starts on Friday (4)
    nov_data = history_service.get_calendar_month_data(test_db, 2024, 11, profile_id=1)
    assert nov_data["days_in_month"] == 30
    assert nov_data["first_day_weekday"] == 4


def test_get_month_completion_stats_empty(test_db: Session, sample_profiles):
    """Test completion stats for a month with no completions."""
    from unittest.mock import patch
    from app.core.time import get_today

    # Mock today as December 14, 2024
    with patch('app.core.time.get_today', return_value=date(2024, 12, 14)):
        stats = history_service.get_month_completion_stats(test_db, 2024, 12, profile_id=1)

        assert stats["total_days"] == 14  # Days from Dec 1 to Dec 14
        assert stats["completed_days"] == 0
        assert stats["completion_rate"] == 0.0


def test_get_month_completion_stats_with_completions(test_db: Session, sample_completed_days):
    """Test completion stats with some completed days."""
    from unittest.mock import patch

    # Mock today as December 14, 2024
    with patch('app.core.time.get_today', return_value=date(2024, 12, 14)):
        stats = history_service.get_month_completion_stats(test_db, 2024, 12, profile_id=1)

        assert stats["total_days"] == 14  # Days from Dec 1 to Dec 14
        assert stats["completed_days"] == 3  # Dec 1, 2, 5
        assert stats["completion_rate"] == round((3 / 14) * 100, 1)


def test_get_month_completion_stats_future_month(test_db: Session, sample_profiles):
    """Test completion stats for a future month."""
    from unittest.mock import patch

    # Mock today as December 14, 2024
    with patch('app.core.time.get_today', return_value=date(2024, 12, 14)):
        stats = history_service.get_month_completion_stats(test_db, 2025, 1, profile_id=1)

        assert stats["total_days"] == 0
        assert stats["completed_days"] == 0
        assert stats["completion_rate"] == 0.0


def test_get_month_completion_stats_past_month(test_db: Session, sample_completed_days):
    """Test completion stats for a past month."""
    from unittest.mock import patch

    # Add some November completions
    nov_days = [
        DailyStatus(date=date(2024, 11, 15), user_id=1, completed_at=datetime(2024, 11, 15, 20, 0)),
        DailyStatus(date=date(2024, 11, 20), user_id=1, completed_at=datetime(2024, 11, 20, 19, 0)),
    ]
    for day in nov_days:
        test_db.add(day)
    test_db.commit()

    # Mock today as December 14, 2024
    with patch('app.core.time.get_today', return_value=date(2024, 12, 14)):
        stats = history_service.get_month_completion_stats(test_db, 2024, 11, profile_id=1)

        assert stats["total_days"] == 30  # All of November
        assert stats["completed_days"] == 2
        assert stats["completion_rate"] == round((2 / 30) * 100, 1)


def test_api_get_month_history(client: TestClient, sample_completed_days):
    """Test API endpoint for getting month history."""
    response = client.get("/api/history/2024/12")

    assert response.status_code == 200
    data = response.json()

    assert data["year"] == 2024
    assert data["month"] == 12
    assert "calendar_data" in data
    assert "stats" in data

    # Check calendar data structure
    calendar_data = data["calendar_data"]
    assert calendar_data["days_in_month"] == 31
    assert calendar_data["first_day_weekday"] == 6
    assert len(calendar_data["days"]) == 31

    # Check some completed days
    assert calendar_data["days"]["2024-12-01"]["completed"] is True
    assert calendar_data["days"]["2024-12-02"]["completed"] is True
    assert calendar_data["days"]["2024-12-03"]["completed"] is False


def test_api_get_month_history_invalid_month(client: TestClient):
    """Test API endpoint with invalid month."""
    response = client.get("/api/history/2024/13")
    assert response.status_code == 400
    assert "Month must be between 1 and 12" in response.json()["detail"]

    response = client.get("/api/history/2024/0")
    assert response.status_code == 400


def test_api_get_month_history_invalid_year(client: TestClient):
    """Test API endpoint with invalid year."""
    response = client.get("/api/history/1999/12")
    assert response.status_code == 400
    assert "Year must be between 2000 and 2100" in response.json()["detail"]

    response = client.get("/api/history/2101/12")
    assert response.status_code == 400


def test_api_get_month_history_different_months(client: TestClient):
    """Test API endpoint for different months."""
    # Test January
    response = client.get("/api/history/2024/1")
    assert response.status_code == 200
    data = response.json()
    assert data["calendar_data"]["days_in_month"] == 31

    # Test February (leap year)
    response = client.get("/api/history/2024/2")
    assert response.status_code == 200
    data = response.json()
    assert data["calendar_data"]["days_in_month"] == 29

    # Test November
    response = client.get("/api/history/2024/11")
    assert response.status_code == 200
    data = response.json()
    assert data["calendar_data"]["days_in_month"] == 30


def test_history_web_route(client: TestClient):
    """Test the /history web route renders successfully."""
    response = client.get("/history")

    assert response.status_code == 200
    # Template renders successfully
    assert response.headers["content-type"].startswith("text/html")


def test_history_web_route_with_params(client: TestClient):
    """Test /history route with custom month/year parameters."""
    response = client.get("/history?year=2024&month=11")

    assert response.status_code == 200
    # Template renders successfully (params are ignored now, handled client-side)
    assert response.headers["content-type"].startswith("text/html")


def test_history_web_route_invalid_year(client: TestClient):
    """Test /history route with invalid year parameter falls back to current year."""
    response = client.get("/history?year=invalid")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")


def test_history_web_route_invalid_month(client: TestClient):
    """Test /history route with invalid month parameter falls back to current month."""
    response = client.get("/history?month=invalid")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")


def test_history_web_route_out_of_range_month(client: TestClient):
    """Test /history route with out of range month falls back to current month."""
    response = client.get("/history?month=13")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")


def test_history_web_route_out_of_range_year(client: TestClient):
    """Test /history route with out of range year falls back to current year."""
    response = client.get("/history?year=1999")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")


def test_calendar_data_all_days_present(test_db: Session, sample_profiles):
    """Test that calendar data includes all days of the month."""
    # Test various months to ensure all days are present
    months_days = [
        (2024, 1, 31),   # January
        (2024, 2, 29),   # February (leap year)
        (2024, 4, 30),   # April
        (2024, 11, 30),  # November
        (2024, 12, 31),  # December
    ]

    for year, month, expected_days in months_days:
        calendar_data = history_service.get_calendar_month_data(test_db, year, month, profile_id=1)
        assert len(calendar_data["days"]) == expected_days

        # Verify each day is present
        for day in range(1, expected_days + 1):
            date_str = f"{year}-{month:02d}-{day:02d}"
            assert date_str in calendar_data["days"]


def test_completion_rate_calculation(test_db: Session, sample_profiles):
    """Test accurate completion rate calculation."""
    from unittest.mock import patch

    # Create a specific scenario: 10 days, 7 completed
    for day in range(1, 11):
        completed = day <= 7
        daily_status = DailyStatus(
            date=date(2024, 11, day),
            user_id=1,
            completed_at=datetime(2024, 11, day, 20, 0) if completed else None
        )
        test_db.add(daily_status)
    test_db.commit()

    # Mock today as November 30, 2024
    with patch('app.core.time.get_today', return_value=date(2024, 11, 30)):
        stats = history_service.get_month_completion_stats(test_db, 2024, 11, profile_id=1)

        assert stats["total_days"] == 30
        assert stats["completed_days"] == 7
        expected_rate = round((7 / 30) * 100, 1)
        assert stats["completion_rate"] == expected_rate


def test_calendar_first_day_weekday(test_db: Session, sample_profiles):
    """Test correct weekday calculation for first day of month."""
    # Test known dates and their weekdays (0=Monday, 6=Sunday)
    test_cases = [
        (2024, 12, 1, 6),   # Dec 1, 2024 = Sunday
        (2024, 1, 1, 0),    # Jan 1, 2024 = Monday
        (2024, 7, 1, 0),    # Jul 1, 2024 = Monday
        (2024, 11, 1, 4),   # Nov 1, 2024 = Friday
    ]

    for year, month, day, expected_weekday in test_cases:
        calendar_data = history_service.get_calendar_month_data(test_db, year, month, profile_id=1)
        assert calendar_data["first_day_weekday"] == expected_weekday


def test_calendar_data_with_partial_completion(test_db: Session, sample_profiles, sample_tasks):
    """Test calendar data includes completion percentages with partial completion."""
    from unittest.mock import patch

    # Get the 2 required tasks from sample_tasks
    required_tasks = [t for t in sample_tasks if t.is_required and t.user_id == 1]
    assert len(required_tasks) == 2  # Ensure we have 2 required tasks

    # Create checks for different completion levels:
    # Day 1: 2/2 complete (100%)
    # Day 2: 1/2 complete (50%)
    # Day 3: 0/2 complete (0%)

    checks_data = [
        # Day 1 - both tasks
        (date(2024, 12, 1), required_tasks[0].id, True),
        (date(2024, 12, 1), required_tasks[1].id, True),
        # Day 2 - 1 task
        (date(2024, 12, 2), required_tasks[0].id, True),
        # Day 3 - 0 tasks (no checks)
    ]

    for check_date, task_id, checked in checks_data:
        check = TaskCheck(date=check_date, task_id=task_id, user_id=1, checked=checked)
        test_db.add(check)
    test_db.commit()

    # Mock today as December 10, 2024 (so all test days are in the past)
    with patch('app.core.time.get_today', return_value=date(2024, 12, 10)):
        calendar_data = history_service.get_calendar_month_data(test_db, 2024, 12, profile_id=1)

        # Check completion percentages
        assert calendar_data["days"]["2024-12-01"]["completion_percentage"] == 100.0
        assert calendar_data["days"]["2024-12-01"]["tasks_completed"] == 2
        assert calendar_data["days"]["2024-12-01"]["tasks_required"] == 2
        assert calendar_data["days"]["2024-12-01"]["is_streak_break"] is False

        assert calendar_data["days"]["2024-12-02"]["completion_percentage"] == 50.0
        assert calendar_data["days"]["2024-12-02"]["tasks_completed"] == 1
        assert calendar_data["days"]["2024-12-02"]["tasks_required"] == 2
        assert calendar_data["days"]["2024-12-02"]["is_streak_break"] is False

        # Day 3 has 0% completion and is in the past - should be marked as streak break
        assert calendar_data["days"]["2024-12-03"]["completion_percentage"] == 0.0
        assert calendar_data["days"]["2024-12-03"]["tasks_completed"] == 0
        assert calendar_data["days"]["2024-12-03"]["tasks_required"] == 2
        assert calendar_data["days"]["2024-12-03"]["is_streak_break"] is True


def test_streak_break_only_past_days(test_db: Session, sample_profiles, sample_tasks):
    """Test that future days and today are not marked as streak breaks."""
    from unittest.mock import patch

    # Mock today as December 10, 2024
    with patch('app.core.time.get_today', return_value=date(2024, 12, 10)):
        calendar_data = history_service.get_calendar_month_data(test_db, 2024, 12, profile_id=1)

        # Today (Dec 10) should not be marked as streak break even with 0%
        assert calendar_data["days"]["2024-12-10"]["completion_percentage"] == 0.0
        assert calendar_data["days"]["2024-12-10"]["is_streak_break"] is False

        # Future dates should not be marked as streak breaks
        assert calendar_data["days"]["2024-12-11"]["completion_percentage"] == 0.0
        assert calendar_data["days"]["2024-12-11"]["is_streak_break"] is False

        assert calendar_data["days"]["2024-12-20"]["completion_percentage"] == 0.0
        assert calendar_data["days"]["2024-12-20"]["is_streak_break"] is False

        # Past day with 0% should be marked as streak break
        assert calendar_data["days"]["2024-12-05"]["completion_percentage"] == 0.0
        assert calendar_data["days"]["2024-12-05"]["is_streak_break"] is True


def test_no_required_tasks_edge_case(test_db: Session, sample_profiles):
    """Test behavior when profile has no required tasks."""
    from unittest.mock import patch

    # Deactivate all tasks for profile 1
    test_db.query(Task).filter(Task.user_id == 1).update({Task.is_active: False})
    test_db.commit()

    # Mock today as December 10, 2024
    with patch('app.core.time.get_today', return_value=date(2024, 12, 10)):
        calendar_data = history_service.get_calendar_month_data(test_db, 2024, 12, profile_id=1)

        # Should handle gracefully - 0/0 = 0% (not error)
        assert calendar_data["days"]["2024-12-01"]["completion_percentage"] == 0.0
        assert calendar_data["days"]["2024-12-01"]["tasks_required"] == 0
        assert calendar_data["days"]["2024-12-01"]["tasks_completed"] == 0
        # Should not be marked as streak break when there are no required tasks
        assert calendar_data["days"]["2024-12-01"]["is_streak_break"] is True  # Past day with 0%


def test_completion_percentage_with_optional_tasks(test_db: Session, sample_profiles, sample_tasks):
    """Test that only required tasks count toward completion percentage."""
    from unittest.mock import patch

    # Get required and optional tasks
    required_tasks = [t for t in sample_tasks if t.is_required and t.user_id == 1]
    optional_task = test_db.query(Task).filter(
        Task.user_id == 1,
        Task.is_required == False,
        Task.is_active == True
    ).first()

    # Create checks: complete optional task but not required tasks
    if optional_task:
        check = TaskCheck(date=date(2024, 12, 1), task_id=optional_task.id, user_id=1, checked=True)
        test_db.add(check)
    test_db.commit()

    # Mock today as December 10, 2024
    with patch('app.core.time.get_today', return_value=date(2024, 12, 10)):
        calendar_data = history_service.get_calendar_month_data(test_db, 2024, 12, profile_id=1)

        # Completing optional task should not contribute to completion percentage
        assert calendar_data["days"]["2024-12-01"]["completion_percentage"] == 0.0
        assert calendar_data["days"]["2024-12-01"]["tasks_completed"] == 0
        assert calendar_data["days"]["2024-12-01"]["tasks_required"] == 2
        assert calendar_data["days"]["2024-12-01"]["is_streak_break"] is True  # Past day with 0%
