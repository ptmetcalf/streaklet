from sqlalchemy.orm import Session
from app.models.daily_status import DailyStatus
from datetime import date
from calendar import monthrange
from typing import Dict, Any


def get_calendar_month_data(db: Session, year: int, month: int) -> Dict[str, Any]:
    """
    Get calendar data for a specific month.

    Returns:
    - days_in_month: number of days in the month
    - first_day_weekday: weekday of first day (0=Monday, 6=Sunday)
    - days: dict mapping date strings to completion status
    """
    # Get first and last day of month
    first_day = date(year, month, 1)
    days_in_month = monthrange(year, month)[1]
    last_day = date(year, month, days_in_month)

    # Get first day weekday (0=Monday in Python)
    first_day_weekday = first_day.weekday()

    # Query all daily statuses for the month
    completed_days = db.query(DailyStatus).filter(
        DailyStatus.date >= first_day,
        DailyStatus.date <= last_day
    ).all()

    # Create a map of date -> completion status
    completed_dates = {
        status.date.isoformat(): {
            'completed': status.completed_at is not None,
            'completed_at': status.completed_at.isoformat() if status.completed_at else None
        }
        for status in completed_days
    }

    # Build days dictionary with all dates in month
    days_dict = {}
    for day in range(1, days_in_month + 1):
        day_date = date(year, month, day)
        date_str = day_date.isoformat()

        if date_str in completed_dates:
            days_dict[date_str] = completed_dates[date_str]
        else:
            # Date exists but not completed
            days_dict[date_str] = {
                'completed': False,
                'completed_at': None
            }

    return {
        'days_in_month': days_in_month,
        'first_day_weekday': first_day_weekday,
        'days': days_dict
    }


def get_month_completion_stats(db: Session, year: int, month: int) -> Dict[str, Any]:
    """
    Get completion statistics for a month.

    Returns:
    - total_days: total days in month up to today
    - completed_days: number of completed days
    - completion_rate: percentage of days completed
    """
    from app.core.time import get_today

    first_day = date(year, month, 1)
    days_in_month = monthrange(year, month)[1]
    last_day = date(year, month, days_in_month)
    today = get_today()

    # Only count days up to today
    end_date = min(last_day, today)

    if first_day > today:
        return {
            'total_days': 0,
            'completed_days': 0,
            'completion_rate': 0
        }

    # Count total days that should be evaluated
    total_days = (end_date - first_day).days + 1

    # Count completed days
    completed_count = db.query(DailyStatus).filter(
        DailyStatus.date >= first_day,
        DailyStatus.date <= end_date,
        DailyStatus.completed_at.isnot(None)
    ).count()

    completion_rate = (completed_count / total_days * 100) if total_days > 0 else 0

    return {
        'total_days': total_days,
        'completed_days': completed_count,
        'completion_rate': round(completion_rate, 1)
    }
