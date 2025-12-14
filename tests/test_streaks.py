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
