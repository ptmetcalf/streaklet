"""API routes for scheduled tasks."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.core.db import get_db
from app.core.profile_context import get_profile_id
from app.core.time import get_today
from app.schemas.task import TaskResponse
from app.services import scheduled_tasks

router = APIRouter(prefix="/api/scheduled", tags=["scheduled"])


@router.get("/due-today", response_model=List[TaskResponse])
def list_scheduled_tasks_due_today(
    db: Session = Depends(get_db),
    profile_id: int = Depends(get_profile_id)
):
    """List scheduled tasks due today.

    Args:
        db: Database session
        profile_id: User profile ID

    Returns:
        List of scheduled tasks due today
    """
    today = get_today()
    return scheduled_tasks.get_scheduled_tasks_due_on_date(db, today, profile_id)


@router.get("/upcoming", response_model=List[TaskResponse])
def list_upcoming_scheduled_tasks(
    days_ahead: int = 30,
    db: Session = Depends(get_db),
    profile_id: int = Depends(get_profile_id)
):
    """List upcoming scheduled tasks.

    Args:
        days_ahead: Number of days to look ahead (default: 30)
        db: Database session
        profile_id: User profile ID

    Returns:
        List of upcoming scheduled tasks
    """
    return scheduled_tasks.get_upcoming_scheduled_tasks(db, profile_id, days_ahead)
