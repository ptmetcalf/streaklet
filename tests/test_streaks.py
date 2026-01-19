import pytest
from sqlalchemy.orm import Session
from datetime import date, timedelta, datetime
from app.services import streaks as streak_service
from app.services import checks as check_service
from app.models.daily_status import DailyStatus


def test_no_streak_on_empty_db(test_db: Session, sample_profiles):
    """Test that streak is 0 when no days are completed."""
    streak_count, last_date = streak_service.calculate_current_streak(test_db, profile_id=1)
    assert streak_count == 0
    assert last_date is None


def test_single_day_streak(test_db: Session, sample_profiles):
    """Test streak of 1 for a single completed day."""
    today = date.today()
    status = DailyStatus(date=today, user_id=1, completed_at=datetime.now())
    test_db.add(status)
    test_db.commit()

    streak_count, last_date = streak_service.calculate_current_streak(test_db, profile_id=1)
    assert streak_count == 1
    assert last_date == today


def test_consecutive_days_streak(test_db: Session, sample_profiles):
    """Test streak increments for consecutive days."""
    today = date.today()

    for i in range(5):
        day = today - timedelta(days=i)
        status = DailyStatus(date=day, user_id=1, completed_at=datetime.now())
        test_db.add(status)
    test_db.commit()

    streak_count, last_date = streak_service.calculate_current_streak(test_db, profile_id=1)
    assert streak_count == 5
    assert last_date == today


def test_streak_resets_on_missed_day(test_db: Session, sample_profiles):
    """Test streak resets when a day is missed."""
    today = date.today()

    status1 = DailyStatus(date=today, user_id=1, completed_at=datetime.now())
    status2 = DailyStatus(date=today - timedelta(days=1), user_id=1, completed_at=datetime.now())
    test_db.add(status1)
    test_db.add(status2)
    test_db.commit()

    streak_count, last_date = streak_service.calculate_current_streak(test_db, profile_id=1)
    assert streak_count == 2

    status3 = DailyStatus(date=today - timedelta(days=4), user_id=1, completed_at=datetime.now())
    test_db.add(status3)
    test_db.commit()

    streak_count, last_date = streak_service.calculate_current_streak(test_db, profile_id=1)
    assert streak_count == 2


def test_get_streak_info(test_db: Session, sample_tasks):
    """Test getting comprehensive streak information."""
    today = date.today()

    yesterday = today - timedelta(days=1)
    status = DailyStatus(date=yesterday, user_id=1, completed_at=datetime.now())
    test_db.add(status)
    test_db.commit()

    check_service.ensure_checks_exist_for_date(test_db, today, profile_id=1)
    check_service.update_task_check(test_db, today, 1, True, profile_id=1)
    check_service.update_task_check(test_db, today, 2, True, profile_id=1)

    streak_info = streak_service.get_streak_info(test_db, profile_id=1)

    assert streak_info["current_streak"] == 2
    assert streak_info["today_complete"] is True
    assert streak_info["today_date"] == today
    assert streak_info["last_completed_date"] == today


def test_today_incomplete_shows_previous_streak(test_db: Session, sample_profiles):
    """Test that incomplete today still shows previous streak."""
    today = date.today()
    yesterday = today - timedelta(days=1)

    for i in range(3):
        day = yesterday - timedelta(days=i)
        status = DailyStatus(date=day, user_id=1, completed_at=datetime.now())
        test_db.add(status)
    test_db.commit()

    streak_info = streak_service.get_streak_info(test_db, profile_id=1)

    assert streak_info["current_streak"] == 3
    assert streak_info["today_complete"] is False
    assert streak_info["last_completed_date"] == yesterday


def test_task_streak_no_checks(test_db: Session, sample_tasks):
    """Test that task streak is 0 when task has no checks."""
    streak_count, last_date = streak_service.calculate_task_streak(test_db, task_id=1, profile_id=1)
    assert streak_count == 0
    assert last_date is None


def test_task_streak_consecutive_days(test_db: Session, sample_tasks):
    """Test per-task streak counts consecutive completions."""
    today = date.today()

    # Create checks for 5 consecutive days for task 1
    for i in range(5):
        day = today - timedelta(days=i)
        check_service.ensure_checks_exist_for_date(test_db, day, profile_id=1)
        check_service.update_task_check(test_db, day, task_id=1, checked=True, profile_id=1)

    streak_count, last_date = streak_service.calculate_task_streak(test_db, task_id=1, profile_id=1)
    assert streak_count == 5
    assert last_date == today


def test_task_streak_with_gap(test_db: Session, sample_tasks):
    """Test streak resets after missed day."""
    today = date.today()

    # Check days 1-3
    for i in range(3):
        day = today - timedelta(days=i)
        check_service.ensure_checks_exist_for_date(test_db, day, profile_id=1)
        check_service.update_task_check(test_db, day, task_id=1, checked=True, profile_id=1)

    # Skip day 4 (today - 3)

    # Check day 5 (today - 4)
    day5 = today - timedelta(days=4)
    check_service.ensure_checks_exist_for_date(test_db, day5, profile_id=1)
    check_service.update_task_check(test_db, day5, task_id=1, checked=True, profile_id=1)

    # Streak should only count the most recent consecutive days (1-3)
    streak_count, last_date = streak_service.calculate_task_streak(test_db, task_id=1, profile_id=1)
    assert streak_count == 3
    assert last_date == today


def test_task_streak_different_tasks(test_db: Session, sample_tasks):
    """Test multiple tasks have independent streaks."""
    today = date.today()

    # Task 1: 10 consecutive days
    for i in range(10):
        day = today - timedelta(days=i)
        check_service.ensure_checks_exist_for_date(test_db, day, profile_id=1)
        check_service.update_task_check(test_db, day, task_id=1, checked=True, profile_id=1)

    # Task 2: 3 consecutive days
    for i in range(3):
        day = today - timedelta(days=i)
        check_service.ensure_checks_exist_for_date(test_db, day, profile_id=1)
        check_service.update_task_check(test_db, day, task_id=2, checked=True, profile_id=1)

    streak1, _ = streak_service.calculate_task_streak(test_db, task_id=1, profile_id=1)
    streak2, _ = streak_service.calculate_task_streak(test_db, task_id=2, profile_id=1)

    assert streak1 == 10
    assert streak2 == 3


def test_task_streak_broken_returns_zero(test_db: Session, sample_tasks):
    """Test streak returns 0 when more than 1 day since last check."""
    today = date.today()

    # Check task 5 days ago (gap > 1 day)
    old_day = today - timedelta(days=5)
    check_service.ensure_checks_exist_for_date(test_db, old_day, profile_id=1)
    check_service.update_task_check(test_db, old_day, task_id=1, checked=True, profile_id=1)

    streak_count, last_date = streak_service.calculate_task_streak(test_db, task_id=1, profile_id=1)
    assert streak_count == 0
    assert last_date == old_day


def test_task_streak_profile_isolation(test_db: Session, sample_profiles, sample_tasks):
    """Test task streaks are isolated by profile."""
    from app.models.task import Task

    today = date.today()

    # Profile 1: 5 day streak on task 1
    for i in range(5):
        day = today - timedelta(days=i)
        check_service.ensure_checks_exist_for_date(test_db, day, profile_id=1)
        check_service.update_task_check(test_db, day, task_id=1, checked=True, profile_id=1)

    # Create a task for profile 2
    past_date = date(2025, 1, 1)
    task_p2 = Task(
        id=10,
        user_id=2,
        title="Profile 2 Task",
        sort_order=1,
        is_required=True,
        is_active=True,
        active_since=past_date
    )
    test_db.add(task_p2)
    test_db.commit()

    # Profile 2: 2 day streak on task 10
    for i in range(2):
        day = today - timedelta(days=i)
        check_service.ensure_checks_exist_for_date(test_db, day, profile_id=2)
        check_service.update_task_check(test_db, day, task_id=10, checked=True, profile_id=2)

    streak1 = streak_service.calculate_task_streak(test_db, task_id=1, profile_id=1)
    streak2 = streak_service.calculate_task_streak(test_db, task_id=10, profile_id=2)

    assert streak1[0] == 5
    assert streak2[0] == 2
