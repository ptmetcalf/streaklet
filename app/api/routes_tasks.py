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
async def create_task(
    task: TaskCreate,
    db: Session = Depends(get_db),
    profile_id: int = Depends(get_profile_id)
):
    """Create a new task for a profile."""
    new_task = task_service.create_task(db, task, profile_id)

    # If this is a Fitbit task with auto-check enabled, evaluate it immediately for today
    if new_task.fitbit_auto_check and new_task.fitbit_metric_type:
        from app.core.time import get_today
        from app.services.fitbit_checks import evaluate_and_apply_auto_checks
        from app.services import checks as check_service

        today = get_today()
        # Ensure check record exists for the new task
        check_service.ensure_checks_exist_for_date(db, today, profile_id)
        # Evaluate auto-check
        await evaluate_and_apply_auto_checks(db, profile_id, today)

    return new_task


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task: TaskUpdate,
    db: Session = Depends(get_db),
    profile_id: int = Depends(get_profile_id)
):
    """Update a task for a profile."""
    updated_task = task_service.update_task(db, task_id, task, profile_id)
    if not updated_task:
        raise HTTPException(status_code=404, detail="Task not found")

    # If this is a Fitbit task with auto-check enabled, evaluate it immediately for today
    if updated_task.fitbit_auto_check and updated_task.fitbit_metric_type:
        from app.core.time import get_today
        from app.services.fitbit_checks import evaluate_and_apply_auto_checks
        from app.services import checks as check_service

        today = get_today()
        # Ensure check record exists for the task
        check_service.ensure_checks_exist_for_date(db, today, profile_id)
        # Evaluate auto-check
        await evaluate_and_apply_auto_checks(db, profile_id, today)

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
