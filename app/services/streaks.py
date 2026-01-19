from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.daily_status import DailyStatus
from app.models.task_check import TaskCheck
from app.core.time import get_today
from datetime import date, timedelta
from typing import Optional, Tuple


def calculate_current_streak(db: Session, profile_id: int) -> tuple[int, Optional[date]]:
    """
    Calculate the current streak for a profile.
    Returns (streak_count, last_completed_date).

    Logic:
    - Find the most recent date with completed_at not null
    - Count consecutive prior dates with completed_at not null
    - Return that count as current_streak
    """
    completed_days = db.query(DailyStatus).filter(
        and_(
            DailyStatus.completed_at.isnot(None),
            DailyStatus.user_id == profile_id
        )
    ).order_by(DailyStatus.date.desc()).all()

    if not completed_days:
        return 0, None

    last_completed = completed_days[0]
    last_completed_date = last_completed.date

    streak = 1
    current_date = last_completed_date - timedelta(days=1)

    for day_status in completed_days[1:]:
        if day_status.date == current_date:
            streak += 1
            current_date -= timedelta(days=1)
        else:
            break

    return streak, last_completed_date


def calculate_task_streak(db: Session, task_id: int, profile_id: int) -> Tuple[int, Optional[date]]:
    """
    Calculate the current consecutive streak for a specific task.

    Logic mirrors calculate_current_streak() but filtered by task_id:
    1. Find most recent date where this task was checked
    2. Count backwards for consecutive prior days with checked=True
    3. Stop at first gap or beginning of records

    Returns:
        (streak_count, last_completed_date)
    """
    # Get all completed checks for this task, ordered newest first
    completed_checks = db.query(TaskCheck).filter(
        and_(
            TaskCheck.task_id == task_id,
            TaskCheck.user_id == profile_id,
            TaskCheck.checked == True
        )
    ).order_by(TaskCheck.date.desc()).all()

    if not completed_checks:
        return (0, None)

    # Start from most recent completion
    last_completed_date = completed_checks[0].date
    today = get_today()

    # If last completion was today or yesterday, count backwards
    days_since_last = (today - last_completed_date).days

    # If more than 1 day since last check, streak is broken
    if days_since_last > 1:
        return (0, last_completed_date)

    # Count consecutive days backwards
    streak_count = 0
    current_date = last_completed_date

    check_dates = {check.date for check in completed_checks}

    while current_date in check_dates:
        streak_count += 1
        current_date -= timedelta(days=1)

    return (streak_count, last_completed_date)


def get_streak_info(db: Session, profile_id: int) -> dict:
    """
    Get comprehensive streak information for a profile including:
    - current_streak: number of consecutive completed days
    - today_complete: whether today is complete
    - last_completed_date: the most recent completed date
    - today_date: today's date in app timezone
    """
    today = get_today()
    streak_count, last_completed_date = calculate_current_streak(db, profile_id)

    today_status = db.query(DailyStatus).filter(
        and_(
            DailyStatus.date == today,
            DailyStatus.user_id == profile_id
        )
    ).first()
    today_complete = today_status is not None and today_status.completed_at is not None

    return {
        "current_streak": streak_count,
        "today_complete": today_complete,
        "last_completed_date": last_completed_date,
        "today_date": today
    }
