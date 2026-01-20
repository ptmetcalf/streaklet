import pytest
from sqlalchemy.orm import Session
from app.services import checks as check_service
from app.services import tasks as task_service
from app.models.task import Task
from app.models.daily_status import DailyStatus
from app.core.time import get_today


def test_ensure_checks_exist(test_db: Session, sample_tasks):
    """Test that checks are created for all active tasks."""
    today = get_today()
    check_service.ensure_checks_exist_for_date(test_db, today, profile_id=1)

    checks = check_service.get_checks_for_date(test_db, today, profile_id=1)
    assert len(checks) == 3


def test_update_task_check(test_db: Session, sample_tasks):
    """Test checking a task."""
    today = get_today()
    check_service.ensure_checks_exist_for_date(test_db, today, profile_id=1)

    check = check_service.update_task_check(test_db, today, 1, True, profile_id=1)

    assert check.checked is True
    assert check.checked_at is not None


def test_uncheck_task(test_db: Session, sample_tasks):
    """Test unchecking a task."""
    today = get_today()
    check_service.ensure_checks_exist_for_date(test_db, today, profile_id=1)

    check_service.update_task_check(test_db, today, 1, True, profile_id=1)
    check = check_service.update_task_check(test_db, today, 1, False, profile_id=1)

    assert check.checked is False
    assert check.checked_at is None


def test_day_completion_all_required(test_db: Session, sample_tasks):
    """Test that completing all required tasks marks day as complete."""
    today = get_today()
    check_service.ensure_checks_exist_for_date(test_db, today, profile_id=1)

    check_service.update_task_check(test_db, today, 1, True, profile_id=1)
    assert not check_service.is_day_complete(test_db, today, profile_id=1)

    check_service.update_task_check(test_db, today, 2, True, profile_id=1)
    assert check_service.is_day_complete(test_db, today, profile_id=1)

    daily_status = test_db.query(DailyStatus).filter(
        DailyStatus.date == today,
        DailyStatus.user_id == 1
    ).first()
    assert daily_status is not None
    assert daily_status.completed_at is not None


def test_unchecking_clears_completion(test_db: Session, sample_tasks):
    """Test that unchecking a required task clears completion."""
    today = get_today()
    check_service.ensure_checks_exist_for_date(test_db, today, profile_id=1)

    check_service.update_task_check(test_db, today, 1, True, profile_id=1)
    check_service.update_task_check(test_db, today, 2, True, profile_id=1)
    assert check_service.is_day_complete(test_db, today, profile_id=1)

    check_service.update_task_check(test_db, today, 1, False, profile_id=1)
    assert not check_service.is_day_complete(test_db, today, profile_id=1)

    daily_status = test_db.query(DailyStatus).filter(
        DailyStatus.date == today,
        DailyStatus.user_id == 1
    ).first()
    assert daily_status.completed_at is None


def test_optional_tasks_not_required(test_db: Session, sample_tasks):
    """Test that optional tasks don't affect completion."""
    today = get_today()
    check_service.ensure_checks_exist_for_date(test_db, today, profile_id=1)

    check_service.update_task_check(test_db, today, 1, True, profile_id=1)
    check_service.update_task_check(test_db, today, 2, True, profile_id=1)

    assert check_service.is_day_complete(test_db, today, profile_id=1)
