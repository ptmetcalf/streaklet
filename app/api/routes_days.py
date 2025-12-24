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

    # Get Fitbit progress for tasks with Fitbit goals
    from app.services.fitbit_checks import get_task_fitbit_progress

    tasks_with_checks = []
    for task in active_tasks:
        check = checks_map.get(task.id)

        # Get Fitbit progress if task has Fitbit goal
        fitbit_progress = {}
        if task.fitbit_metric_type and task.fitbit_goal_value:
            fitbit_progress = get_task_fitbit_progress(db, task, today, profile_id)

        tasks_with_checks.append(
            TaskWithCheck(
                id=task.id,
                title=task.title,
                sort_order=task.sort_order,
                is_required=task.is_required,
                is_active=task.is_active,
                checked=check.checked if check else False,
                checked_at=check.checked_at if check else None,
                # Fitbit fields
                fitbit_metric_type=task.fitbit_metric_type,
                fitbit_goal_value=task.fitbit_goal_value,
                fitbit_goal_operator=task.fitbit_goal_operator,
                fitbit_auto_check=task.fitbit_auto_check,
                # Fitbit progress
                fitbit_current_value=fitbit_progress.get("current_value"),
                fitbit_goal_met=fitbit_progress.get("goal_met", False),
                fitbit_unit=fitbit_progress.get("unit"),
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
