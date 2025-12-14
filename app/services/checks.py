from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.task_check import TaskCheck
from app.models.task import Task
from app.models.daily_status import DailyStatus
from app.core.time import get_now
from datetime import date
from typing import List, Optional


def get_task_check(db: Session, check_date: date, task_id: int) -> Optional[TaskCheck]:
    """Get a task check for a specific date and task."""
    return db.query(TaskCheck).filter(
        and_(TaskCheck.date == check_date, TaskCheck.task_id == task_id)
    ).first()


def get_checks_for_date(db: Session, check_date: date) -> List[TaskCheck]:
    """Get all task checks for a specific date."""
    return db.query(TaskCheck).filter(TaskCheck.date == check_date).all()


def ensure_checks_exist_for_date(db: Session, check_date: date) -> None:
    """Ensure task checks exist for all active tasks on a given date."""
    active_tasks = db.query(Task).filter(Task.is_active == True).all()
    existing_checks = {check.task_id: check for check in get_checks_for_date(db, check_date)}

    for task in active_tasks:
        if task.id not in existing_checks:
            new_check = TaskCheck(
                date=check_date,
                task_id=task.id,
                checked=False,
                checked_at=None
            )
            db.add(new_check)

    db.commit()


def update_task_check(db: Session, check_date: date, task_id: int, checked: bool) -> Optional[TaskCheck]:
    """Update a task check and recompute daily completion status."""
    check = get_task_check(db, check_date, task_id)

    if not check:
        check = TaskCheck(
            date=check_date,
            task_id=task_id,
            checked=checked,
            checked_at=get_now() if checked else None
        )
        db.add(check)
    else:
        check.checked = checked
        check.checked_at = get_now() if checked else None

    db.commit()
    db.refresh(check)

    recompute_daily_completion(db, check_date)

    return check


def recompute_daily_completion(db: Session, check_date: date) -> None:
    """
    Recompute whether a day is complete based on required tasks.
    A day is complete if all required, active tasks are checked.
    """
    active_required_tasks = db.query(Task).filter(
        and_(Task.is_active == True, Task.is_required == True)
    ).all()

    required_task_ids = {task.id for task in active_required_tasks}

    if not required_task_ids:
        all_complete = True
    else:
        checks = get_checks_for_date(db, check_date)
        checked_task_ids = {check.task_id for check in checks if check.checked}
        all_complete = required_task_ids.issubset(checked_task_ids)

    daily_status = db.query(DailyStatus).filter(DailyStatus.date == check_date).first()

    if all_complete:
        if not daily_status:
            daily_status = DailyStatus(date=check_date, completed_at=get_now())
            db.add(daily_status)
        elif daily_status.completed_at is None:
            daily_status.completed_at = get_now()
    else:
        if daily_status and daily_status.completed_at is not None:
            daily_status.completed_at = None

    db.commit()


def is_day_complete(db: Session, check_date: date) -> bool:
    """Check if a specific day is complete."""
    daily_status = db.query(DailyStatus).filter(DailyStatus.date == check_date).first()
    return daily_status is not None and daily_status.completed_at is not None
