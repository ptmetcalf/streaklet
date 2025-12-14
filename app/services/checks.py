from sqlalchemy.orm import Session
from sqlalchemy import and_
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
    """Ensure task checks exist for all active tasks on a given date for a profile."""
    active_tasks = db.query(Task).filter(
        and_(
            Task.is_active == True,
            Task.user_id == profile_id
        )
    ).all()
    existing_checks = {check.task_id: check for check in get_checks_for_date(db, check_date, profile_id)}

    for task in active_tasks:
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

    recompute_daily_completion(db, check_date, profile_id)

    return check


def recompute_daily_completion(db: Session, check_date: date, profile_id: int) -> None:
    """
    Recompute whether a day is complete based on required tasks for a profile.
    A day is complete if all required, active tasks are checked.
    """
    active_required_tasks = db.query(Task).filter(
        and_(
            Task.is_active == True,
            Task.is_required == True,
            Task.user_id == profile_id
        )
    ).all()

    required_task_ids = {task.id for task in active_required_tasks}

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
