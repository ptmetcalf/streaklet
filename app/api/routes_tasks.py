from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.db import get_db
from app.core.profile_context import get_profile_id
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse
from app.services import tasks as task_service

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("", response_model=List[TaskResponse])
def list_tasks(
    db: Session = Depends(get_db),
    profile_id: int = Depends(get_profile_id)
):
    """List all tasks for a profile ordered by sort_order."""
    return task_service.get_tasks(db, profile_id)


@router.post("", response_model=TaskResponse, status_code=201)
def create_task(
    task: TaskCreate,
    db: Session = Depends(get_db),
    profile_id: int = Depends(get_profile_id)
):
    """Create a new task for a profile."""
    return task_service.create_task(db, task, profile_id)


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    task: TaskUpdate,
    db: Session = Depends(get_db),
    profile_id: int = Depends(get_profile_id)
):
    """Update a task for a profile."""
    updated_task = task_service.update_task(db, task_id, task, profile_id)
    if not updated_task:
        raise HTTPException(status_code=404, detail="Task not found")
    return updated_task


@router.delete("/{task_id}", status_code=204)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    profile_id: int = Depends(get_profile_id)
):
    """Delete a task for a profile."""
    success = task_service.delete_task(db, task_id, profile_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return None
