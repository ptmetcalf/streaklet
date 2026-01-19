from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.models.task_check import TaskCheck
from app.models.task import Task
from app.models.daily_status import DailyStatus
from app.core.time import get_now
from datetime import date
from typing import List, Optional


def get_task_check(db: Session, check_date: date, task_id: int, profile_id: int) -> Optional[TaskCheck]:
    """Get a task check for a specific date and task for a profile."""
    return db.query(TaskCheck).filter(
        and_(
            TaskCheck.date == check_date,
            TaskCheck.task_id == task_id,
            TaskCheck.user_id == profile_id
        )
    ).first()


def get_checks_for_date(db: Session, check_date: date, profile_id: int) -> List[TaskCheck]:
    """Get all task checks for a specific date for a profile."""
    return db.query(TaskCheck).filter(
        and_(
            TaskCheck.date == check_date,
            TaskCheck.user_id == profile_id
        )
    ).all()


def ensure_checks_exist_for_date(db: Session, check_date: date, profile_id: int) -> None:
    """
    Create TaskCheck records for applicable tasks on a date.
    - Daily tasks: always
    - Scheduled tasks: only if due on this date
    - Punch list: never (created on completion)
    """
    # Get daily tasks
    daily_tasks = db.query(Task).filter(
        and_(
            Task.is_active == True,
            Task.user_id == profile_id,
            Task.task_type == 'daily'
        )
    ).all()

    # Get scheduled tasks due on this date
    scheduled_tasks_due = db.query(Task).filter(
        and_(
            Task.is_active == True,
            Task.user_id == profile_id,
            Task.task_type == 'scheduled',
            Task.next_occurrence_date == check_date
        )
    ).all()

    applicable_tasks = daily_tasks + scheduled_tasks_due
    existing_checks = {check.task_id: check for check in get_checks_for_date(db, check_date, profile_id)}

    for task in applicable_tasks:
        if task.id not in existing_checks:
            new_check = TaskCheck(
                date=check_date,
                task_id=task.id,
                user_id=profile_id,
                checked=False,
                checked_at=None
            )
            db.add(new_check)

    db.commit()


def update_task_check(db: Session, check_date: date, task_id: int, checked: bool, profile_id: int) -> Optional[TaskCheck]:
    """Update a task check and recompute daily completion status for a profile."""
    # Get the task to check its type
    task = db.query(Task).filter(
        and_(
            Task.id == task_id,
            Task.user_id == profile_id
        )
    ).first()

    if not task:
        return None

    check = get_task_check(db, check_date, task_id, profile_id)

    if not check:
        check = TaskCheck(
            date=check_date,
            task_id=task_id,
            user_id=profile_id,
            checked=checked,
            checked_at=get_now() if checked else None
        )
        db.add(check)
    else:
        check.checked = checked
        check.checked_at = get_now() if checked else None

    db.commit()
    db.refresh(check)

    # If scheduled task marked complete, update occurrence dates
    if task.task_type == 'scheduled' and checked:
        from app.services.scheduled_tasks import complete_scheduled_occurrence
        complete_scheduled_occurrence(db, task_id, check_date, profile_id)

    # Recompute daily completion (punch list tasks don't affect this)
    if task.task_type != 'punch_list':
        recompute_daily_completion(db, check_date, profile_id)

    return check


def recompute_daily_completion(db: Session, check_date: date, profile_id: int) -> None:
    """
    Recompute whether a day is complete.
    Only considers:
    - Daily tasks (always)
    - Scheduled tasks (if due on this date)
    Does NOT consider punch list tasks.
    """
    # Get required tasks that count toward daily completion
    required_tasks = db.query(Task).filter(
        and_(
            Task.is_active == True,
            Task.is_required == True,
            Task.user_id == profile_id,
            or_(
                Task.task_type == 'daily',
                and_(
                    Task.task_type == 'scheduled',
                    Task.next_occurrence_date == check_date
                )
            )
        )
    ).all()

    required_task_ids = {task.id for task in required_tasks}

    if not required_task_ids:
        all_complete = True
    else:
        checks = get_checks_for_date(db, check_date, profile_id)
        checked_task_ids = {check.task_id for check in checks if check.checked}
        all_complete = required_task_ids.issubset(checked_task_ids)

    daily_status = db.query(DailyStatus).filter(
        and_(
            DailyStatus.date == check_date,
            DailyStatus.user_id == profile_id
        )
    ).first()

    if all_complete:
        if not daily_status:
            daily_status = DailyStatus(date=check_date, user_id=profile_id, completed_at=get_now())
            db.add(daily_status)
        elif daily_status.completed_at is None:
            daily_status.completed_at = get_now()
    else:
        if daily_status and daily_status.completed_at is not None:
            daily_status.completed_at = None

    db.commit()


def is_day_complete(db: Session, check_date: date, profile_id: int) -> bool:
    """Check if a specific day is complete for a profile."""
    daily_status = db.query(DailyStatus).filter(
        and_(
            DailyStatus.date == check_date,
            DailyStatus.user_id == profile_id
        )
    ).first()
    return daily_status is not None and daily_status.completed_at is not None
