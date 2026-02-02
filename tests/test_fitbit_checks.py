"""Tests for Fitbit auto-check service."""
import pytest
from datetime import date
from sqlalchemy.orm import Session

from app.services import fitbit_checks
from app.models.task import Task
from app.models.fitbit_metric import FitbitMetric
from app.services import checks as check_service
from app.core.time import get_today


def test_evaluate_goal_gte():
    """Test goal evaluation with 'greater than or equal' operator."""
    assert fitbit_checks.evaluate_goal(10000, 10000, "gte") is True
    assert fitbit_checks.evaluate_goal(10001, 10000, "gte") is True
    assert fitbit_checks.evaluate_goal(9999, 10000, "gte") is False


def test_evaluate_goal_lte():
    """Test goal evaluation with 'less than or equal' operator."""
    assert fitbit_checks.evaluate_goal(60, 65, "lte") is True
    assert fitbit_checks.evaluate_goal(65, 65, "lte") is True
    assert fitbit_checks.evaluate_goal(70, 65, "lte") is False


def test_evaluate_goal_eq():
    """Test goal evaluation with 'equals' operator."""
    assert fitbit_checks.evaluate_goal(100, 100, "eq") is True
    assert fitbit_checks.evaluate_goal(99, 100, "eq") is False
    assert fitbit_checks.evaluate_goal(101, 100, "eq") is False


def test_evaluate_goal_invalid_operator():
    """Test goal evaluation with invalid operator returns False."""
    assert fitbit_checks.evaluate_goal(100, 100, "invalid") is False


@pytest.mark.asyncio
async def test_evaluate_and_apply_auto_checks_goal_met(test_db: Session, sample_profiles):
    """Test that tasks are auto-checked when Fitbit goals are met."""
    today = get_today()

    # Create task with Fitbit goal
    task = Task(
        user_id=1,
        title="Walk 10,000 steps",
        sort_order=1,
        is_required=True,
        is_active=True,
        fitbit_metric_type="steps",
        fitbit_goal_value=10000,
        fitbit_goal_operator="gte",
        fitbit_auto_check=True,
    active_since=date(2025, 1, 1)
    )
    test_db.add(task)
    test_db.commit()

    # Create Fitbit metric showing goal was met
    metric = FitbitMetric(
        user_id=1,
        date=today,
        metric_type="steps",
        value=12500,
        unit="steps"
    )
    test_db.add(metric)
    test_db.commit()

    # Ensure checks exist
    check_service.ensure_checks_exist_for_date(test_db, today, profile_id=1)

    # Run auto-check
    result = await fitbit_checks.evaluate_and_apply_auto_checks(test_db, 1, today)

    assert result["tasks_evaluated"] == 1
    assert result["tasks_checked"] == 1

    # Verify task was checked
    checks = check_service.get_checks_for_date(test_db, today, profile_id=1)
    task_check = next((c for c in checks if c.task_id == task.id), None)
    assert task_check is not None
    assert task_check.checked is True


@pytest.mark.asyncio
async def test_evaluate_and_apply_auto_checks_goal_not_met(test_db: Session, sample_profiles):
    """Test that tasks are not checked when Fitbit goals are not met."""
    today = get_today()

    # Create task with Fitbit goal
    task = Task(
        user_id=1,
        title="Walk 10,000 steps",
        sort_order=1,
        is_required=True,
        is_active=True,
        fitbit_metric_type="steps",
        fitbit_goal_value=10000,
        fitbit_goal_operator="gte",
        fitbit_auto_check=True,
    active_since=date(2025, 1, 1)
    )
    test_db.add(task)
    test_db.commit()

    # Create Fitbit metric showing goal was NOT met
    metric = FitbitMetric(
        user_id=1,
        date=today,
        metric_type="steps",
        value=8000,
        unit="steps"
    )
    test_db.add(metric)
    test_db.commit()

    # Ensure checks exist
    check_service.ensure_checks_exist_for_date(test_db, today, profile_id=1)

    # Run auto-check
    result = await fitbit_checks.evaluate_and_apply_auto_checks(test_db, 1, today)

    assert result["tasks_evaluated"] == 1
    assert result["tasks_checked"] == 0

    # Verify task was NOT checked
    checks = check_service.get_checks_for_date(test_db, today, profile_id=1)
    task_check = next((c for c in checks if c.task_id == task.id), None)
    assert task_check is not None
    assert task_check.checked is False


@pytest.mark.asyncio
async def test_evaluate_and_apply_auto_checks_unchecks_when_goal_lost(test_db: Session, sample_profiles):
    """Test that tasks are unchecked when previously met goals are no longer met."""
    today = get_today()

    # Create task with Fitbit goal
    task = Task(
        user_id=1,
        title="Walk 10,000 steps",
        sort_order=1,
        is_required=True,
        is_active=True,
        fitbit_metric_type="steps",
        fitbit_goal_value=10000,
        fitbit_goal_operator="gte",
        fitbit_auto_check=True,
    active_since=date(2025, 1, 1)
    )
    test_db.add(task)
    test_db.commit()

    # Ensure checks exist and manually check the task
    check_service.ensure_checks_exist_for_date(test_db, today, profile_id=1)
    check_service.update_task_check(test_db, today, task.id, checked=True, profile_id=1)

    # Create Fitbit metric showing goal is NO LONGER met
    metric = FitbitMetric(
        user_id=1,
        date=today,
        metric_type="steps",
        value=5000,
        unit="steps"
    )
    test_db.add(metric)
    test_db.commit()

    # Run auto-check
    result = await fitbit_checks.evaluate_and_apply_auto_checks(test_db, 1, today)

    assert result["tasks_evaluated"] == 1
    # Should uncheck the task since goal is no longer met
    assert result["tasks_checked"] == 0

    # Verify task was unchecked
    checks = check_service.get_checks_for_date(test_db, today, profile_id=1)
    task_check = next((c for c in checks if c.task_id == task.id), None)
    assert task_check is not None
    assert task_check.checked is False


@pytest.mark.asyncio
async def test_evaluate_and_apply_auto_checks_skips_disabled_tasks(test_db: Session, sample_profiles):
    """Test that tasks with auto-check disabled are not evaluated."""
    today = get_today()

    # Create task with Fitbit goal but auto-check disabled
    task = Task(
        user_id=1,
        title="Walk 10,000 steps",
        sort_order=1,
        is_required=True,
        is_active=True,
        fitbit_metric_type="steps",
        fitbit_goal_value=10000,
        fitbit_goal_operator="gte",
        fitbit_auto_check=False,  # Disabled
        active_since=date(2025, 1, 1)
    )
    test_db.add(task)
    test_db.commit()

    # Create Fitbit metric showing goal was met
    metric = FitbitMetric(
        user_id=1,
        date=today,
        metric_type="steps",
        value=12500,
        unit="steps"
    )
    test_db.add(metric)
    test_db.commit()

    # Run auto-check
    result = await fitbit_checks.evaluate_and_apply_auto_checks(test_db, 1, today)

    assert result["tasks_evaluated"] == 0
    assert result["tasks_checked"] == 0


@pytest.mark.asyncio
async def test_evaluate_and_apply_auto_checks_no_metric_data(test_db: Session, sample_profiles):
    """Test behavior when no Fitbit metric data exists for the date."""
    today = get_today()

    # Create task with Fitbit goal
    task = Task(
        user_id=1,
        title="Walk 10,000 steps",
        sort_order=1,
        is_required=True,
        is_active=True,
        fitbit_metric_type="steps",
        fitbit_goal_value=10000,
        fitbit_goal_operator="gte",
        fitbit_auto_check=True,
    active_since=date(2025, 1, 1)
    )
    test_db.add(task)
    test_db.commit()

    # NO Fitbit metric created

    # Run auto-check
    result = await fitbit_checks.evaluate_and_apply_auto_checks(test_db, 1, today)

    assert result["tasks_evaluated"] == 1
    assert result["tasks_checked"] == 0


@pytest.mark.asyncio
async def test_get_task_fitbit_progress(test_db: Session, sample_profiles):
    """Test getting Fitbit progress for a task."""
    today = get_today()

    # Create task with Fitbit goal
    task = Task(
        user_id=1,
        title="Walk 10,000 steps",
        sort_order=1,
        is_required=True,
        is_active=True,
        fitbit_metric_type="steps",
        fitbit_goal_value=10000,
        fitbit_goal_operator="gte",
        fitbit_auto_check=True,
    active_since=date(2025, 1, 1)
    )
    test_db.add(task)
    test_db.commit()

    # Create Fitbit metric
    metric = FitbitMetric(
        user_id=1,
        date=today,
        metric_type="steps",
        value=7543,
        unit="steps"
    )
    test_db.add(metric)
    test_db.commit()

    # Get progress
    progress = fitbit_checks.get_task_fitbit_progress(test_db, task, today, profile_id=1)

    assert progress["current_value"] == 7543
    assert progress["unit"] == "steps"
    assert progress["goal_met"] is False


@pytest.mark.asyncio
async def test_get_task_fitbit_progress_goal_met(test_db: Session, sample_profiles):
    """Test getting Fitbit progress when goal is met."""
    today = get_today()

    task = Task(
        user_id=1,
        title="Walk 10,000 steps",
        sort_order=1,
        is_required=True,
        is_active=True,
        fitbit_metric_type="steps",
        fitbit_goal_value=10000,
        fitbit_goal_operator="gte",
        fitbit_auto_check=False,
    active_since=date(2025, 1, 1)
    )
    test_db.add(task)
    test_db.commit()

    metric = FitbitMetric(
        user_id=1,
        date=today,
        metric_type="steps",
        value=12500,
        unit="steps"
    )
    test_db.add(metric)
    test_db.commit()

    progress = fitbit_checks.get_task_fitbit_progress(test_db, task, today, profile_id=1)

    assert progress["current_value"] == 12500
    assert progress["goal_met"] is True


@pytest.mark.asyncio
async def test_get_task_fitbit_progress_no_data(test_db: Session, sample_profiles):
    """Test getting Fitbit progress when no metric data exists."""
    today = get_today()

    task = Task(
        user_id=1,
        title="Walk 10,000 steps",
        sort_order=1,
        is_required=True,
        is_active=True,
        fitbit_metric_type="steps",
        fitbit_goal_value=10000,
        fitbit_goal_operator="gte",
        fitbit_auto_check=False,
    active_since=date(2025, 1, 1)
    )
    test_db.add(task)
    test_db.commit()

    # No metric created

    progress = fitbit_checks.get_task_fitbit_progress(test_db, task, today, profile_id=1)

    # When no data, should return None for current_value but include goal_value
    assert progress["current_value"] is None
    assert progress["goal_value"] == 10000
    assert progress["goal_met"] is False


@pytest.mark.asyncio
async def test_evaluate_and_apply_auto_checks_excludes_punch_list(test_db: Session, sample_profiles):
    """Test that punch_list tasks are never auto-checked by Fitbit."""
    today = get_today()

    # Create punch_list task with Fitbit goal
    task = Task(
        user_id=1,
        title="Organize garage",
        task_type="punch_list",
        sort_order=1,
        is_required=False,
        is_active=True,
        fitbit_metric_type="steps",
        fitbit_goal_value=10000,
        fitbit_goal_operator="gte",
        fitbit_auto_check=True,
        active_since=date(2025, 1, 1)
    )
    test_db.add(task)
    test_db.commit()

    # Create Fitbit metric showing goal was met
    metric = FitbitMetric(
        user_id=1,
        date=today,
        metric_type="steps",
        value=12500,
        unit="steps"
    )
    test_db.add(metric)
    test_db.commit()

    # Run auto-check
    result = await fitbit_checks.evaluate_and_apply_auto_checks(test_db, 1, today)

    # Punch list tasks should not be evaluated
    assert result["tasks_evaluated"] == 0
    assert result["tasks_checked"] == 0


@pytest.mark.asyncio
async def test_evaluate_and_apply_auto_checks_excludes_future_tasks(test_db: Session, sample_profiles):
    """Test that tasks with future active_since dates are not auto-checked."""
    today = get_today()
    from datetime import timedelta

    # Create task with future active_since date
    future_date = today + timedelta(days=7)
    task = Task(
        user_id=1,
        title="Future task",
        task_type="daily",
        sort_order=1,
        is_required=True,
        is_active=True,
        fitbit_metric_type="steps",
        fitbit_goal_value=10000,
        fitbit_goal_operator="gte",
        fitbit_auto_check=True,
        active_since=future_date
    )
    test_db.add(task)
    test_db.commit()

    # Create Fitbit metric showing goal was met
    metric = FitbitMetric(
        user_id=1,
        date=today,
        metric_type="steps",
        value=12500,
        unit="steps"
    )
    test_db.add(metric)
    test_db.commit()

    # Run auto-check
    result = await fitbit_checks.evaluate_and_apply_auto_checks(test_db, 1, today)

    # Future tasks should not be evaluated
    assert result["tasks_evaluated"] == 0
    assert result["tasks_checked"] == 0


@pytest.mark.asyncio
async def test_evaluate_and_apply_auto_checks_includes_scheduled(test_db: Session, sample_profiles):
    """Test that scheduled tasks ARE auto-checked by Fitbit."""
    today = get_today()

    # Create scheduled task with Fitbit goal
    task = Task(
        user_id=1,
        title="Weekly workout goal",
        task_type="scheduled",
        sort_order=1,
        is_required=True,
        is_active=True,
        fitbit_metric_type="steps",
        fitbit_goal_value=10000,
        fitbit_goal_operator="gte",
        fitbit_auto_check=True,
        active_since=date(2025, 1, 1)
    )
    test_db.add(task)
    test_db.commit()

    # Create Fitbit metric showing goal was met
    metric = FitbitMetric(
        user_id=1,
        date=today,
        metric_type="steps",
        value=12500,
        unit="steps"
    )
    test_db.add(metric)
    test_db.commit()

    # Ensure checks exist
    check_service.ensure_checks_exist_for_date(test_db, today, profile_id=1)

    # Run auto-check
    result = await fitbit_checks.evaluate_and_apply_auto_checks(test_db, 1, today)

    # Scheduled tasks should be evaluated and checked
    assert result["tasks_evaluated"] == 1
    assert result["tasks_checked"] == 1


@pytest.mark.asyncio
async def test_evaluate_and_apply_auto_checks_includes_null_active_since(test_db: Session, sample_profiles):
    """Test that legacy tasks with NULL active_since are still auto-checked."""
    today = get_today()

    # Create task with NULL active_since (legacy)
    task = Task(
        user_id=1,
        title="Legacy task",
        task_type="daily",
        sort_order=1,
        is_required=True,
        is_active=True,
        fitbit_metric_type="steps",
        fitbit_goal_value=10000,
        fitbit_goal_operator="gte",
        fitbit_auto_check=True,
        active_since=None
    )
    test_db.add(task)
    test_db.commit()

    # Create Fitbit metric showing goal was met
    metric = FitbitMetric(
        user_id=1,
        date=today,
        metric_type="steps",
        value=12500,
        unit="steps"
    )
    test_db.add(metric)
    test_db.commit()

    # Ensure checks exist
    check_service.ensure_checks_exist_for_date(test_db, today, profile_id=1)

    # Run auto-check
    result = await fitbit_checks.evaluate_and_apply_auto_checks(test_db, 1, today)

    # Legacy tasks should be evaluated and checked
    assert result["tasks_evaluated"] == 1
    assert result["tasks_checked"] == 1
