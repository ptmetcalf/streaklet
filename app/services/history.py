from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.daily_status import DailyStatus
from app.models.fitbit_metric import FitbitMetric
from app.models.task import Task
from app.models.task_check import TaskCheck
from datetime import date
from calendar import monthrange
from typing import Dict, Any, Optional, Set


def get_calendar_month_data(db: Session, year: int, month: int, profile_id: int) -> Dict[str, Any]:
    """
    Get calendar data for a specific month for a profile.

    Returns:
    - days_in_month: number of days in the month
    - first_day_weekday: weekday of first day (0=Monday, 6=Sunday)
    - days: dict mapping date strings to completion status with percentage data
    """
    from app.core.time import get_today

    # Get first and last day of month
    first_day = date(year, month, 1)
    days_in_month = monthrange(year, month)[1]
    last_day = date(year, month, days_in_month)
    today = get_today()

    # Get first day weekday (0=Monday in Python)
    first_day_weekday = first_day.weekday()

    # Query all daily statuses for the month for this profile
    completed_days = db.query(DailyStatus).filter(
        and_(
            DailyStatus.date >= first_day,
            DailyStatus.date <= last_day,
            DailyStatus.user_id == profile_id
        )
    ).all()

    # Create a map of date -> completion status
    completed_dates = {
        status.date.isoformat(): {
            'completed': status.completed_at is not None,
            'completed_at': status.completed_at.isoformat() if status.completed_at else None
        }
        for status in completed_days
    }

    # Get all required active tasks for the profile (current state)
    required_tasks = db.query(Task).filter(
        and_(
            Task.user_id == profile_id,
            Task.is_active == True,
            Task.is_required == True
        )
    ).all()
    required_task_ids: Set[int] = {task.id for task in required_tasks}
    total_required = len(required_task_ids)

    # Get all task checks for the month
    task_checks = db.query(TaskCheck).filter(
        and_(
            TaskCheck.user_id == profile_id,
            TaskCheck.date >= first_day,
            TaskCheck.date <= last_day,
            TaskCheck.checked == True
        )
    ).all()

    # Group checks by date and count completed required tasks
    checks_by_date: Dict[date, Set[int]] = {}
    for check in task_checks:
        if check.date not in checks_by_date:
            checks_by_date[check.date] = set()
        if check.task_id in required_task_ids:
            checks_by_date[check.date].add(check.task_id)

    # Query Fitbit metrics for the month
    fitbit_metrics = db.query(FitbitMetric).filter(
        and_(
            FitbitMetric.user_id == profile_id,
            FitbitMetric.date >= first_day,
            FitbitMetric.date <= last_day
        )
    ).all()

    # Organize Fitbit metrics by date
    fitbit_by_date: Dict[str, Dict[str, Any]] = {}
    for metric in fitbit_metrics:
        date_str = metric.date.isoformat()
        if date_str not in fitbit_by_date:
            fitbit_by_date[date_str] = {}
        fitbit_by_date[date_str][metric.metric_type] = {
            'value': metric.value,
            'unit': metric.unit
        }

    # Build days dictionary with all dates in month
    days_dict = {}
    for day in range(1, days_in_month + 1):
        day_date = date(year, month, day)
        date_str = day_date.isoformat()

        # Calculate completion metrics
        tasks_completed = len(checks_by_date.get(day_date, set()))
        completion_percentage = (tasks_completed / total_required * 100) if total_required > 0 else 0

        # Mark as streak break if 0% completion and in the past
        is_streak_break = (completion_percentage == 0) and (day_date < today)

        if date_str in completed_dates:
            days_dict[date_str] = completed_dates[date_str]
        else:
            # Date exists but not completed
            days_dict[date_str] = {
                'completed': False,
                'completed_at': None
            }

        # Add completion percentage data
        days_dict[date_str]['completion_percentage'] = round(completion_percentage, 1)
        days_dict[date_str]['tasks_completed'] = tasks_completed
        days_dict[date_str]['tasks_required'] = total_required
        days_dict[date_str]['is_streak_break'] = is_streak_break

        # Add Fitbit metrics if available
        if date_str in fitbit_by_date:
            days_dict[date_str]['fitbit_metrics'] = fitbit_by_date[date_str]

    return {
        'days_in_month': days_in_month,
        'first_day_weekday': first_day_weekday,
        'days': days_dict
    }


def get_month_completion_stats(db: Session, year: int, month: int, profile_id: int) -> Dict[str, Any]:
    """
    Get completion statistics for a month for a profile.

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

    # Count completed days for this profile
    completed_count = db.query(DailyStatus).filter(
        and_(
            DailyStatus.date >= first_day,
            DailyStatus.date <= end_date,
            DailyStatus.completed_at.isnot(None),
            DailyStatus.user_id == profile_id
        )
    ).count()

    completion_rate = (completed_count / total_days * 100) if total_days > 0 else 0

    return {
        'total_days': total_days,
        'completed_days': completed_count,
        'completion_rate': round(completion_rate, 1)
    }
