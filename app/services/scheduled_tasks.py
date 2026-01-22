"""Service for scheduled task logic and recurrence calculations."""

from datetime import date, timedelta
from typing import List, Optional
import calendar
from sqlalchemy.orm import Session

from app.models.task import Task
from app.core.time import get_today


def calculate_next_occurrence(task: Task, from_date: Optional[date] = None) -> Optional[date]:
    """Calculate next occurrence based on recurrence pattern.

    Args:
        task: Task with recurrence_pattern
        from_date: Calculate from this date (defaults to today)

    Returns:
        Next occurrence date or None if no pattern
    """
    if not task.recurrence_pattern:
        return None

    pattern = task.recurrence_pattern
    pattern_type = pattern.get('type')
    interval = pattern.get('interval', 1)

    start = from_date or get_today()

    if pattern_type == 'days':
        # Every N days
        return start + timedelta(days=interval)

    elif pattern_type == 'weekly':
        # Weekly on specific day (0=Monday, 6=Sunday)
        day_of_week = pattern.get('day_of_week', 0)
        days_ahead = (day_of_week - start.weekday()) % 7

        # If today is the target day, schedule for next week
        if days_ahead == 0:
            days_ahead = 7 * interval
        else:
            # Calculate weeks to skip
            days_ahead += 7 * (interval - 1)

        return start + timedelta(days=days_ahead)

    elif pattern_type == 'monthly':
        # Monthly on specific day of month
        day_of_month = pattern.get('day_of_month', 1)
        next_month = start.month + interval
        next_year = start.year

        # Handle year rollover
        while next_month > 12:
            next_month -= 12
            next_year += 1

        # Handle edge cases (Feb 31 -> last day of month)
        max_day = calendar.monthrange(next_year, next_month)[1]
        safe_day = min(day_of_month, max_day)

        return date(next_year, next_month, safe_day)

    return None


def get_scheduled_tasks_due_on_date(db: Session, check_date: date, profile_id: int) -> List[Task]:
    """Get scheduled tasks due on specific date.

    Args:
        db: Database session
        check_date: Date to check for due tasks
        profile_id: User profile ID

    Returns:
        List of tasks due on the specified date
    """
    return db.query(Task).filter(
        Task.user_id == profile_id,
        Task.is_active .is_(True),
        Task.task_type == 'scheduled',
        Task.next_occurrence_date == check_date
    ).order_by(Task.sort_order).all()


def get_upcoming_scheduled_tasks(db: Session, profile_id: int, days_ahead: int = 30) -> List[Task]:
    """Get scheduled tasks due within the next N days.

    Args:
        db: Database session
        profile_id: User profile ID
        days_ahead: Number of days to look ahead

    Returns:
        List of upcoming scheduled tasks
    """
    today = get_today()
    end_date = today + timedelta(days=days_ahead)

    return db.query(Task).filter(
        Task.user_id == profile_id,
        Task.is_active .is_(True),
        Task.task_type == 'scheduled',
        Task.next_occurrence_date.isnot(None),
        Task.next_occurrence_date >= today,
        Task.next_occurrence_date <= end_date
    ).order_by(Task.next_occurrence_date, Task.sort_order).all()


def complete_scheduled_occurrence(db: Session, task_id: int, check_date: date, profile_id: int) -> Optional[Task]:
    """Mark scheduled task complete and calculate next occurrence.

    Args:
        db: Database session
        task_id: Task ID
        check_date: Date of completion
        profile_id: User profile ID

    Returns:
        Updated task or None if not found
    """
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == profile_id
    ).first()

    if not task or task.task_type != 'scheduled':
        return None

    # Update task occurrence dates
    task.last_occurrence_date = check_date

    # Determine which date to calculate from based on schedule mode
    if task.schedule_mode == 'rolling':
        # Rolling: calculate from completion date
        # This allows flexible completion and resets the interval from when completed
        task.next_occurrence_date = calculate_next_occurrence(task, from_date=check_date)
    else:
        # Calendar mode (default): calculate from scheduled date
        # This prevents early completion from making task reappear sooner
        # If completed early, next occurrence is still the next scheduled date
        base_date = task.next_occurrence_date or check_date
        task.next_occurrence_date = calculate_next_occurrence(task, from_date=base_date)

    db.commit()
    db.refresh(task)
    return task


def update_scheduled_tasks_daily(db: Session):
    """Recalculate next_occurrence_date for all scheduled tasks.

    This should be run as a daily maintenance job to ensure
    next_occurrence_date is always up-to-date.

    Args:
        db: Database session
    """
    today = get_today()

    scheduled_tasks = db.query(Task).filter(
        Task.is_active .is_(True),
        Task.task_type == 'scheduled'
    ).all()

    for task in scheduled_tasks:
        # Recalculate if next occurrence is None or in the past
        if task.next_occurrence_date is None or task.next_occurrence_date < today:
            task.next_occurrence_date = calculate_next_occurrence(task)

    db.commit()


def is_task_overdue(task: Task, check_date: Optional[date] = None) -> bool:
    """Check if a scheduled task is overdue.

    Args:
        task: Task to check
        check_date: Date to check against (defaults to today)

    Returns:
        True if task is overdue, False otherwise
    """
    if not task or task.task_type != 'scheduled':
        return False

    today = check_date or get_today()

    # Task is overdue if next_occurrence_date is in the past
    if task.next_occurrence_date and task.next_occurrence_date < today:
        return True

    return False


def get_days_overdue(task: Task, check_date: Optional[date] = None) -> int:
    """Calculate how many days overdue a task is.

    Args:
        task: Task to check
        check_date: Date to check against (defaults to today)

    Returns:
        Number of days overdue, or 0 if not overdue
    """
    if not is_task_overdue(task, check_date):
        return 0

    today = check_date or get_today()
    days_diff = (today - task.next_occurrence_date).days

    return max(0, days_diff)
