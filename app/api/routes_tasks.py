from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.db import get_db
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse
from app.services import tasks as task_service

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("", response_model=List[TaskResponse])
def list_tasks(db: Session = Depends(get_db)):
    """List all tasks ordered by sort_order."""
    return task_service.get_tasks(db)


@router.post("", response_model=TaskResponse, status_code=201)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    """Create a new task."""
    return task_service.create_task(db, task)


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, task: TaskUpdate, db: Session = Depends(get_db)):
    """Update a task."""
    updated_task = task_service.update_task(db, task_id, task)
    if not updated_task:
        raise HTTPException(status_code=404, detail="Task not found")
    return updated_task


@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """Delete a task."""
    success = task_service.delete_task(db, task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return None
