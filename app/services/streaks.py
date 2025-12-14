from sqlalchemy.orm import Session
from app.models.daily_status import DailyStatus
from app.core.time import get_today
from datetime import date, timedelta
from typing import Optional


def calculate_current_streak(db: Session) -> tuple[int, Optional[date]]:
    """
    Calculate the current streak.
    Returns (streak_count, last_completed_date).

    Logic:
    - Find the most recent date with completed_at not null
    - Count consecutive prior dates with completed_at not null
    - Return that count as current_streak
    """
    completed_days = db.query(DailyStatus).filter(
        DailyStatus.completed_at.isnot(None)
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


def get_streak_info(db: Session) -> dict:
    """
    Get comprehensive streak information including:
    - current_streak: number of consecutive completed days
    - today_complete: whether today is complete
    - last_completed_date: the most recent completed date
    - today_date: today's date in app timezone
    """
    today = get_today()
    streak_count, last_completed_date = calculate_current_streak(db)

    today_status = db.query(DailyStatus).filter(DailyStatus.date == today).first()
    today_complete = today_status is not None and today_status.completed_at is not None

    return {
        "current_streak": streak_count,
        "today_complete": today_complete,
        "last_completed_date": last_completed_date,
        "today_date": today
    }
