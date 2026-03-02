"""Compatibility service for legacy shopping-list endpoints."""

from typing import Optional

from sqlalchemy.orm import Session

from app.models.task import Task
from app.schemas.task import TaskCreate
from app.schemas.custom_list import CustomListItemCreate
from app.services import custom_lists


def list_shopping_items(db: Session, profile_id: int, include_completed: bool = True) -> list[Task]:
    shopping_list = custom_lists.get_or_create_shopping_list(db, profile_id)
    return custom_lists.list_custom_list_items(
        db,
        list_id=shopping_list.id,
        profile_id=profile_id,
        include_completed=include_completed,
    )


def create_shopping_item(db: Session, item: TaskCreate, profile_id: int) -> Optional[Task]:
    shopping_list = custom_lists.get_or_create_shopping_list(db, profile_id)
    payload = CustomListItemCreate(title=item.title, icon=item.icon)
    return custom_lists.create_custom_list_item(db, shopping_list.id, payload, profile_id)


def complete_shopping_item(db: Session, item_id: int, profile_id: int) -> Optional[Task]:
    shopping_list = custom_lists.get_or_create_shopping_list(db, profile_id)
    return custom_lists.complete_custom_list_item(db, shopping_list.id, item_id, profile_id)


def uncomplete_shopping_item(db: Session, item_id: int, profile_id: int) -> Optional[Task]:
    shopping_list = custom_lists.get_or_create_shopping_list(db, profile_id)
    return custom_lists.uncomplete_custom_list_item(db, shopping_list.id, item_id, profile_id)


def delete_shopping_item(db: Session, item_id: int, profile_id: int) -> bool:
    shopping_list = custom_lists.get_or_create_shopping_list(db, profile_id)
    return custom_lists.delete_custom_list_item(db, shopping_list.id, item_id, profile_id)
