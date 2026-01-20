"""Service for punch list task operations."""

from datetime import timedelta
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.task import Task
from app.models.task_check import TaskCheck
from app.core.time import get_now, get_today


def get_active_punch_list_tasks(db: Session, profile_id: int, include_archived: bool = False) -> List[Task]:
    """Get punch list tasks, optionally including archived.

    Args:
        db: Database session
        profile_id: User profile ID
        include_archived: If True, include archived tasks

    Returns:
        List of punch list tasks sorted by priority
        (overdue, then due soon, then no due date, then created_at)
    """
    query = db.query(Task).filter(
        Task.user_id == profile_id,
        Task.is_active .is_(True),
        Task.task_type == 'punch_list'
    )

    if not include_archived:
        query = query.filter(Task.archived_at.is_(None))

    # Sort: overdue first, then by due date, then by created_at
    return query.order_by(
        Task.due_date.is_(None),
        Task.due_date,
        Task.created_at
    ).all()


def complete_punch_list_task(db: Session, task_id: int, profile_id: int) -> Optional[Task]:
    """Mark punch list task as complete.

    Args:
        db: Database session
        task_id: Task ID
        profile_id: User profile ID

    Returns:
        Updated task or None if not found
    """
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == profile_id
    ).first()

    if not task or task.task_type != 'punch_list':
        return None

    now = get_now()
    today = get_today()

    # Mark complete
    task.completed_at = now

    # Create TaskCheck record for completion date
    check = db.query(TaskCheck).filter(
        TaskCheck.date == today,
        TaskCheck.task_id == task_id,
        TaskCheck.user_id == profile_id
    ).first()

    if not check:
        check = TaskCheck(
            date=today,
            task_id=task_id,
            user_id=profile_id,
            checked=True,
            checked_at=now
        )
        db.add(check)
    else:
        check.checked = True
        check.checked_at = now

    db.commit()
    db.refresh(task)
    return task


def uncomplete_punch_list_task(db: Session, task_id: int, profile_id: int) -> Optional[Task]:
    """Undo completion of punch list task.

    Args:
        db: Database session
        task_id: Task ID
        profile_id: User profile ID

    Returns:
        Updated task or None if not found
    """
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == profile_id
    ).first()

    if not task or task.task_type != 'punch_list':
        return None

    # Remove completion
    task.completed_at = None

    # Remove TaskCheck record
    today = get_today()
    check = db.query(TaskCheck).filter(
        TaskCheck.date == today,
        TaskCheck.task_id == task_id,
        TaskCheck.user_id == profile_id
    ).first()

    if check:
        check.checked = False
        check.checked_at = None

    db.commit()
    db.refresh(task)
    return task


def archive_old_completed_punch_list_tasks(db: Session):
    """Auto-archive punch list tasks completed more than 7 days ago.

    This should be run as a daily maintenance job.

    Args:
        db: Database session
    """
    cutoff_date = get_today() - timedelta(days=7)
    cutoff_datetime = get_now().replace(
        year=cutoff_date.year,
        month=cutoff_date.month,
        day=cutoff_date.day,
        hour=0,
        minute=0,
        second=0,
        microsecond=0
    )

    tasks_to_archive = db.query(Task).filter(
        Task.task_type == 'punch_list',
        Task.completed_at.isnot(None),
        Task.archived_at.is_(None),
        Task.completed_at < cutoff_datetime
    ).all()

    for task in tasks_to_archive:
        task.archived_at = get_now()

    db.commit()


def delete_punch_list_task(db: Session, task_id: int, profile_id: int) -> bool:
    """Delete a punch list task.

    Args:
        db: Database session
        task_id: Task ID
        profile_id: User profile ID

    Returns:
        True if deleted, False if not found
    """
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == profile_id,
        Task.task_type == 'punch_list'
    ).first()

    if not task:
        return False

    db.delete(task)
    db.commit()
    return True
