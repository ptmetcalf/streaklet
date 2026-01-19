"""API routes for punch list tasks."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.db import get_db
from app.core.profile_context import get_profile_id
from app.schemas.task import TaskResponse
from app.services import punch_list

router = APIRouter(prefix="/api/punch-list", tags=["punch-list"])


@router.get("", response_model=List[TaskResponse])
def list_punch_list_tasks(
    include_archived: bool = False,
    db: Session = Depends(get_db),
    profile_id: int = Depends(get_profile_id)
):
    """List punch list tasks for a profile.

    Args:
        include_archived: If True, include archived tasks
        db: Database session
        profile_id: User profile ID

    Returns:
        List of punch list tasks
    """
    return punch_list.get_active_punch_list_tasks(db, profile_id, include_archived)


@router.post("/{task_id}/complete", response_model=TaskResponse)
def complete_punch_list_task(
    task_id: int,
    db: Session = Depends(get_db),
    profile_id: int = Depends(get_profile_id)
):
    """Mark punch list task as complete.

    Args:
        task_id: Task ID
        db: Database session
        profile_id: User profile ID

    Returns:
        Updated task

    Raises:
        HTTPException: If task not found or not a punch list task
    """
    task = punch_list.complete_punch_list_task(db, task_id, profile_id)
    if not task:
        raise HTTPException(status_code=404, detail="Punch list task not found")
    return task


@router.delete("/{task_id}/complete", response_model=TaskResponse)
def uncomplete_punch_list_task(
    task_id: int,
    db: Session = Depends(get_db),
    profile_id: int = Depends(get_profile_id)
):
    """Undo completion of punch list task.

    Args:
        task_id: Task ID
        db: Database session
        profile_id: User profile ID

    Returns:
        Updated task

    Raises:
        HTTPException: If task not found or not a punch list task
    """
    task = punch_list.uncomplete_punch_list_task(db, task_id, profile_id)
    if not task:
        raise HTTPException(status_code=404, detail="Punch list task not found")
    return task


@router.delete("/{task_id}")
def delete_punch_list_task(
    task_id: int,
    db: Session = Depends(get_db),
    profile_id: int = Depends(get_profile_id)
):
    """Delete a punch list task.

    Args:
        task_id: Task ID
        db: Database session
        profile_id: User profile ID

    Returns:
        Success message

    Raises:
        HTTPException: If task not found or not a punch list task
    """
    success = punch_list.delete_punch_list_task(db, task_id, profile_id)
    if not success:
        raise HTTPException(status_code=404, detail="Punch list task not found")
    return {"message": "Task deleted successfully"}
