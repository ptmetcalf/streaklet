"""Service for shopping list item operations."""

from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.task import Task
from app.models.task_check import TaskCheck
from app.schemas.task import TaskCreate
from app.core.time import get_now, get_today


def list_shopping_items(db: Session, profile_id: int, include_completed: bool = True) -> List[Task]:
    """List shopping list items for a profile."""
    query = db.query(Task).filter(
        Task.user_id == profile_id,
        Task.is_active.is_(True),
        Task.task_type == 'shopping_list'
    )

    if not include_completed:
        query = query.filter(Task.completed_at.is_(None))

    return query.order_by(
        Task.completed_at.isnot(None),
        Task.created_at.desc()
    ).all()


def create_shopping_item(db: Session, item: TaskCreate, profile_id: int) -> Task:
    """Create a new shopping list item for a profile."""
    from app.services.tasks import get_default_task_icon

    item_data = item.model_dump()
    item_data['task_type'] = 'shopping_list'
    item_data['is_required'] = False
    item_data['due_date'] = None
    item_data['active_since'] = get_today()

    if item_data.get('icon') is None:
        item_data['icon'] = get_default_task_icon(item_data['title'])

    db_item = Task(**item_data, user_id=profile_id)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def complete_shopping_item(db: Session, item_id: int, profile_id: int) -> Optional[Task]:
    """Mark a shopping list item as purchased."""
    item = db.query(Task).filter(
        Task.id == item_id,
        Task.user_id == profile_id,
        Task.task_type == 'shopping_list'
    ).first()

    if not item:
        return None

    now = get_now()
    today = get_today()

    item.completed_at = now

    check = db.query(TaskCheck).filter(
        TaskCheck.date == today,
        TaskCheck.task_id == item_id,
        TaskCheck.user_id == profile_id
    ).first()

    if not check:
        check = TaskCheck(
            date=today,
            task_id=item_id,
            user_id=profile_id,
            checked=True,
            checked_at=now
        )
        db.add(check)
    else:
        check.checked = True
        check.checked_at = now

    db.commit()
    db.refresh(item)
    return item


def uncomplete_shopping_item(db: Session, item_id: int, profile_id: int) -> Optional[Task]:
    """Mark a shopping list item as not purchased."""
    item = db.query(Task).filter(
        Task.id == item_id,
        Task.user_id == profile_id,
        Task.task_type == 'shopping_list'
    ).first()

    if not item:
        return None

    item.completed_at = None

    today = get_today()
    check = db.query(TaskCheck).filter(
        TaskCheck.date == today,
        TaskCheck.task_id == item_id,
        TaskCheck.user_id == profile_id
    ).first()

    if check:
        check.checked = False
        check.checked_at = None

    db.commit()
    db.refresh(item)
    return item


def delete_shopping_item(db: Session, item_id: int, profile_id: int) -> bool:
    """Delete a shopping list item."""
    item = db.query(Task).filter(
        Task.id == item_id,
        Task.user_id == profile_id,
        Task.task_type == 'shopping_list'
    ).first()

    if not item:
        return False

    db.delete(item)
    db.commit()
    return True
