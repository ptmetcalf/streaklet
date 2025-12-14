from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate
from typing import List, Optional


DEFAULT_TASKS = [
    {"title": "Follow a diet", "sort_order": 1, "is_required": True, "is_active": True},
    {"title": "30 minute workout", "sort_order": 2, "is_required": True, "is_active": True},
    {"title": "30 minute workout", "sort_order": 3, "is_required": True, "is_active": True},
    {"title": "Read 10 pages", "sort_order": 4, "is_required": True, "is_active": True},
    {"title": "20 minutes of hobby time", "sort_order": 5, "is_required": True, "is_active": True},
]


def seed_default_tasks(db: Session) -> None:
    """Seed default tasks if the tasks table is empty."""
    count = db.query(func.count(Task.id)).scalar()
    if count == 0:
        for task_data in DEFAULT_TASKS:
            task = Task(**task_data)
            db.add(task)
        db.commit()


def get_tasks(db: Session) -> List[Task]:
    """Get all tasks ordered by sort_order."""
    return db.query(Task).order_by(Task.sort_order).all()


def get_active_tasks(db: Session) -> List[Task]:
    """Get all active tasks ordered by sort_order."""
    return db.query(Task).filter(Task.is_active == True).order_by(Task.sort_order).all()


def get_task_by_id(db: Session, task_id: int) -> Optional[Task]:
    """Get a task by ID."""
    return db.query(Task).filter(Task.id == task_id).first()


def create_task(db: Session, task: TaskCreate) -> Task:
    """Create a new task."""
    db_task = Task(**task.model_dump())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


def update_task(db: Session, task_id: int, task_update: TaskUpdate) -> Optional[Task]:
    """Update a task."""
    db_task = get_task_by_id(db, task_id)
    if not db_task:
        return None

    update_data = task_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_task, key, value)

    db.commit()
    db.refresh(db_task)
    return db_task


def delete_task(db: Session, task_id: int) -> bool:
    """Delete a task (hard delete)."""
    db_task = get_task_by_id(db, task_id)
    if not db_task:
        return False

    db.delete(db_task)
    db.commit()
    return True
