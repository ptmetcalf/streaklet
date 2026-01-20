"""
Fitbit auto-check service.

Handles:
- Evaluating Fitbit goals for tasks
- Auto-checking tasks when goals are met
- Goal condition logic (gte, lte, eq)
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import date
from typing import Dict

from app.models.task import Task
from app.models.fitbit_metric import FitbitMetric
from app.services import checks as check_service


def evaluate_goal(metric_value: float, goal_value: float, operator: str) -> bool:
    """
    Evaluate if a metric value meets a goal condition.

    Args:
        metric_value: Current metric value
        goal_value: Goal threshold value
        operator: Comparison operator ('gte', 'lte', 'eq')

    Returns:
        True if goal is met, False otherwise
    """
    if operator == 'gte':  # Greater than or equal
        return metric_value >= goal_value
    elif operator == 'lte':  # Less than or equal
        return metric_value <= goal_value
    elif operator == 'eq':  # Equal
        return metric_value == goal_value
    else:
        return False


async def evaluate_and_apply_auto_checks(
    db: Session,
    profile_id: int,
    target_date: date
) -> Dict:
    """
    Evaluate Fitbit goals and auto-check tasks for a specific date.

    Queries all tasks with fitbit_auto_check=True, checks if their goals are met,
    and auto-checks the tasks if conditions are satisfied.

    Args:
        db: Database session
        profile_id: Profile ID
        target_date: Date to evaluate

    Returns:
        Dictionary with evaluation results: {tasks_evaluated, tasks_checked, tasks_unchecked}
    """
    # Get all tasks with auto-check enabled
    tasks = db.query(Task).filter(
        and_(
            Task.user_id == profile_id,
            Task.is_active .is_(True),
            Task.fitbit_auto_check .is_(True),
            Task.fitbit_metric_type.isnot(None)
        )
    ).all()

    tasks_evaluated = 0
    tasks_checked = 0
    tasks_unchecked = 0

    for task in tasks:
        tasks_evaluated += 1

        # Get the metric for this task
        metric = db.query(FitbitMetric).filter(
            and_(
                FitbitMetric.user_id == profile_id,
                FitbitMetric.date == target_date,
                FitbitMetric.metric_type == task.fitbit_metric_type
            )
        ).first()

        # Determine if goal is met
        goal_met = False
        if metric and task.fitbit_goal_value is not None and task.fitbit_goal_operator:
            goal_met = evaluate_goal(
                metric.value,
                task.fitbit_goal_value,
                task.fitbit_goal_operator
            )

        # Auto-check or uncheck task based on goal status
        if goal_met:
            # Check the task
            check_service.update_task_check(
                db,
                target_date,
                task.id,
                checked=True,
                profile_id=profile_id
            )
            tasks_checked += 1
        else:
            # Uncheck the task if it was auto-checked before but goal no longer met
            # (This handles case where Fitbit data updates later in the day)
            existing_check = check_service.get_task_check(db, target_date, task.id, profile_id)
            if existing_check and existing_check.checked:
                check_service.update_task_check(
                    db,
                    target_date,
                    task.id,
                    checked=False,
                    profile_id=profile_id
                )
                tasks_unchecked += 1

    return {
        "tasks_evaluated": tasks_evaluated,
        "tasks_checked": tasks_checked,
        "tasks_unchecked": tasks_unchecked
    }


def get_task_fitbit_progress(
    db: Session,
    task: Task,
    target_date: date,
    profile_id: int
) -> Dict:
    """
    Get Fitbit progress for a task.

    Returns current value, goal value, and whether goal is met.

    Args:
        db: Database session
        task: Task with Fitbit goal
        target_date: Date to check
        profile_id: Profile ID

    Returns:
        Dictionary with progress info: {current_value, goal_value, goal_met, unit}
    """
    if not task.fitbit_metric_type or not task.fitbit_goal_value:
        return {
            "current_value": None,
            "goal_value": None,
            "goal_met": False,
            "unit": None
        }

    # Get metric
    metric = db.query(FitbitMetric).filter(
        and_(
            FitbitMetric.user_id == profile_id,
            FitbitMetric.date == target_date,
            FitbitMetric.metric_type == task.fitbit_metric_type
        )
    ).first()

    if not metric:
        return {
            "current_value": None,
            "goal_value": task.fitbit_goal_value,
            "goal_met": False,
            "unit": None
        }

    # Evaluate goal
    goal_met = False
    if task.fitbit_goal_operator:
        goal_met = evaluate_goal(
            metric.value,
            task.fitbit_goal_value,
            task.fitbit_goal_operator
        )

    return {
        "current_value": metric.value,
        "goal_value": task.fitbit_goal_value,
        "goal_met": goal_met,
        "unit": metric.unit
    }
