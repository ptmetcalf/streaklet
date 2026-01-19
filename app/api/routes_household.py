"""
API routes for household maintenance tracker

CRITICAL ARCHITECTURE NOTE:
Most endpoints do NOT use get_profile_id dependency because household tasks are SHARED.
Only the completion endpoint uses profile_id for attribution (tracking WHO completed a task).
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.db import get_db
from app.core.profile_context import get_profile_id
from app.services import household as household_service
from app.schemas.household import (
    HouseholdTaskCreate,
    HouseholdTaskUpdate,
    HouseholdTaskResponse,
    HouseholdTaskWithStatus,
    HouseholdCompletionCreate,
    HouseholdCompletionResponse
)


router = APIRouter(prefix="/api/household", tags=["household"])


@router.get("/tasks", response_model=List[HouseholdTaskWithStatus])
def list_household_tasks(
    frequency: Optional[str] = Query(None, pattern="^(weekly|monthly|quarterly|annual|todo)$"),
    include_inactive: bool = False,
    db: Session = Depends(get_db)
):
    """
    List all household tasks (SHARED - no profile filtering).

    Args:
        frequency: Optional filter by frequency (weekly/monthly/quarterly/annual)
        include_inactive: Whether to include inactive tasks

    Returns:
        List of household tasks with completion status
    """
    if frequency:
        tasks = household_service.get_household_tasks_by_frequency(db, frequency, include_inactive)
        return [household_service.get_task_with_status(db, task.id) for task in tasks]
    else:
        return household_service.get_all_tasks_with_status(db, include_inactive)


@router.get("/tasks/{task_id}", response_model=HouseholdTaskWithStatus)
def get_household_task(
    task_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a single household task with completion status.

    Args:
        task_id: Household task ID

    Returns:
        Household task with status info
    """
    task = household_service.get_task_with_status(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Household task not found")
    return task


@router.get("/overdue", response_model=List[HouseholdTaskWithStatus])
def get_overdue_tasks(db: Session = Depends(get_db)):
    """
    Get all overdue household tasks.

    Returns:
        List of overdue tasks with status info
    """
    return household_service.get_overdue_tasks(db)


@router.post("/tasks", response_model=HouseholdTaskResponse, status_code=201)
def create_household_task(
    task_data: HouseholdTaskCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new household task (SHARED - no profile association).

    Args:
        task_data: Task creation data

    Returns:
        Created household task
    """
    task = household_service.create_household_task(
        db=db,
        title=task_data.title,
        description=task_data.description,
        frequency=task_data.frequency,
        due_date=task_data.due_date,
        sort_order=task_data.sort_order
    )
    return task


@router.put("/tasks/{task_id}", response_model=HouseholdTaskResponse)
def update_household_task(
    task_id: int,
    task_data: HouseholdTaskUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing household task.

    Args:
        task_id: Task ID to update
        task_data: Updated task data

    Returns:
        Updated household task
    """
    task = household_service.update_household_task(
        db=db,
        task_id=task_id,
        title=task_data.title,
        description=task_data.description,
        frequency=task_data.frequency,
        due_date=task_data.due_date,
        sort_order=task_data.sort_order,
        is_active=task_data.is_active
    )
    if not task:
        raise HTTPException(status_code=404, detail="Household task not found")
    return task


@router.delete("/tasks/{task_id}", status_code=204)
def delete_household_task(
    task_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a household task (cascade deletes completions).

    Args:
        task_id: Task ID to delete

    Returns:
        204 No Content on success
    """
    success = household_service.delete_household_task(db, task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Household task not found")
    return None


@router.post("/tasks/{task_id}/complete", status_code=201)
def mark_task_complete(
    task_id: int,
    completion_data: Optional[HouseholdCompletionCreate] = None,
    db: Session = Depends(get_db),
    profile_id: int = Depends(get_profile_id)  # ONLY endpoint that uses profile_id!
):
    """
    Mark a household task as completed by current profile.

    Args:
        task_id: Household task ID to complete
        completion_data: Optional completion notes
        profile_id: Profile ID (from header) - ATTRIBUTION ONLY

    Returns:
        201 Created on success
    """
    notes = completion_data.notes if completion_data else None
    completion = household_service.mark_task_complete(db, task_id, profile_id, notes)
    if not completion:
        raise HTTPException(status_code=404, detail="Household task not found")
    return {"message": "Task marked complete", "completion_id": completion.id}


@router.get("/tasks/{task_id}/history", response_model=List[HouseholdCompletionResponse])
def get_completion_history(
    task_id: int,
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get completion history for a household task.

    Args:
        task_id: Household task ID
        limit: Maximum number of completions to return (1-100)

    Returns:
        List of completions with profile names
    """
    history = household_service.get_completion_history(db, task_id, limit)
    return history
