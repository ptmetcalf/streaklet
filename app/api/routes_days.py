from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import date
from app.core.db import get_db
from app.core.profile_context import get_profile_id
from app.core.time import get_today
from app.schemas.day import DayResponse, TaskWithCheck
from app.schemas.check import CheckUpdate
from app.services import tasks as task_service
from app.services import checks as check_service
from app.services import streaks as streak_service

router = APIRouter(prefix="/api/days", tags=["days"])


@router.get("/today", response_model=DayResponse)
def get_today_info(
    db: Session = Depends(get_db),
    profile_id: int = Depends(get_profile_id)
):
    """Get today's checklist with all tasks and completion status for a profile."""
    today = get_today()

    check_service.ensure_checks_exist_for_date(db, today, profile_id)

    active_tasks = task_service.get_active_tasks(db, profile_id)
    checks_map = {
        check.task_id: check
        for check in check_service.get_checks_for_date(db, today, profile_id)
    }

    tasks_with_checks = []
    for task in active_tasks:
        check = checks_map.get(task.id)
        tasks_with_checks.append(
            TaskWithCheck(
                id=task.id,
                title=task.title,
                sort_order=task.sort_order,
                is_required=task.is_required,
                is_active=task.is_active,
                checked=check.checked if check else False,
                checked_at=check.checked_at if check else None,
            )
        )

    streak_info = streak_service.get_streak_info(db, profile_id)
    is_complete = check_service.is_day_complete(db, today, profile_id)

    from app.models.daily_status import DailyStatus
    daily_status = db.query(DailyStatus).filter(
        and_(
            DailyStatus.date == today,
            DailyStatus.user_id == profile_id
        )
    ).first()

    return DayResponse(
        date=today,
        tasks=tasks_with_checks,
        all_required_complete=is_complete,
        completed_at=daily_status.completed_at if daily_status else None,
        streak={
            "current_streak": streak_info["current_streak"],
            "today_complete": streak_info["today_complete"],
            "last_completed_date": streak_info["last_completed_date"],
        },
    )


@router.put("/{check_date}/checks/{task_id}")
def update_check(
    check_date: date,
    task_id: int,
    check_update: CheckUpdate,
    db: Session = Depends(get_db),
    profile_id: int = Depends(get_profile_id)
):
    """Toggle a task check for a specific date for a profile."""
    task = task_service.get_task_by_id(db, task_id, profile_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    check = check_service.update_task_check(db, check_date, task_id, check_update.checked, profile_id)
    return {
        "date": check_date,
        "task_id": task_id,
        "checked": check.checked,
        "checked_at": check.checked_at,
    }
