"""API routes for shopping list items."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.db import get_db
from app.core.profile_context import get_profile_id
from app.schemas.task import TaskResponse, TaskCreate
from app.services import shopping_list

router = APIRouter(prefix="/api/shopping-list", tags=["shopping-list"])


@router.get("", response_model=List[TaskResponse])
def list_shopping_items(
    include_completed: bool = True,
    db: Session = Depends(get_db),
    profile_id: int = Depends(get_profile_id)
):
    """List shopping items for a profile."""
    return shopping_list.list_shopping_items(db, profile_id, include_completed)


@router.post("", response_model=TaskResponse, status_code=201)
def create_shopping_item(
    item: TaskCreate,
    db: Session = Depends(get_db),
    profile_id: int = Depends(get_profile_id)
):
    """Create a new shopping item."""
    return shopping_list.create_shopping_item(db, item, profile_id)


@router.post("/{item_id}/complete", response_model=TaskResponse)
def complete_shopping_item(
    item_id: int,
    db: Session = Depends(get_db),
    profile_id: int = Depends(get_profile_id)
):
    """Mark shopping item as complete."""
    item = shopping_list.complete_shopping_item(db, item_id, profile_id)
    if not item:
        raise HTTPException(status_code=404, detail="Shopping list item not found")
    return item


@router.delete("/{item_id}/complete", response_model=TaskResponse)
def uncomplete_shopping_item(
    item_id: int,
    db: Session = Depends(get_db),
    profile_id: int = Depends(get_profile_id)
):
    """Undo completion for shopping item."""
    item = shopping_list.uncomplete_shopping_item(db, item_id, profile_id)
    if not item:
        raise HTTPException(status_code=404, detail="Shopping list item not found")
    return item


@router.delete("/{item_id}")
def delete_shopping_item(
    item_id: int,
    db: Session = Depends(get_db),
    profile_id: int = Depends(get_profile_id)
):
    """Delete shopping item."""
    deleted = shopping_list.delete_shopping_item(db, item_id, profile_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Shopping list item not found")
    return {"message": "Shopping list item deleted successfully"}
