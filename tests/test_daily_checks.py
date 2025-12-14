import pytest
from sqlalchemy.orm import Session
from datetime import date
from app.services import checks as check_service
from app.services import tasks as task_service
from app.models.task import Task
from app.models.daily_status import DailyStatus


def test_ensure_checks_exist(test_db: Session, sample_tasks):
    """Test that checks are created for all active tasks."""
    today = date.today()
    check_service.ensure_checks_exist_for_date(test_db, today)

    checks = check_service.get_checks_for_date(test_db, today)
    assert len(checks) == 3


def test_update_task_check(test_db: Session, sample_tasks):
    """Test checking a task."""
    today = date.today()
    check_service.ensure_checks_exist_for_date(test_db, today)

    check = check_service.update_task_check(test_db, today, 1, True)

    assert check.checked is True
    assert check.checked_at is not None


def test_uncheck_task(test_db: Session, sample_tasks):
    """Test unchecking a task."""
    today = date.today()
    check_service.ensure_checks_exist_for_date(test_db, today)

    check_service.update_task_check(test_db, today, 1, True)
    check = check_service.update_task_check(test_db, today, 1, False)

    assert check.checked is False
    assert check.checked_at is None


def test_day_completion_all_required(test_db: Session, sample_tasks):
    """Test that completing all required tasks marks day as complete."""
    today = date.today()
    check_service.ensure_checks_exist_for_date(test_db, today)

    check_service.update_task_check(test_db, today, 1, True)
    assert not check_service.is_day_complete(test_db, today)

    check_service.update_task_check(test_db, today, 2, True)
    assert check_service.is_day_complete(test_db, today)

    daily_status = test_db.query(DailyStatus).filter(DailyStatus.date == today).first()
    assert daily_status is not None
    assert daily_status.completed_at is not None


def test_unchecking_clears_completion(test_db: Session, sample_tasks):
    """Test that unchecking a required task clears completion."""
    today = date.today()
    check_service.ensure_checks_exist_for_date(test_db, today)

    check_service.update_task_check(test_db, today, 1, True)
    check_service.update_task_check(test_db, today, 2, True)
    assert check_service.is_day_complete(test_db, today)

    check_service.update_task_check(test_db, today, 1, False)
    assert not check_service.is_day_complete(test_db, today)

    daily_status = test_db.query(DailyStatus).filter(DailyStatus.date == today).first()
    assert daily_status.completed_at is None


def test_optional_tasks_not_required(test_db: Session, sample_tasks):
    """Test that optional tasks don't affect completion."""
    today = date.today()
    check_service.ensure_checks_exist_for_date(test_db, today)

    check_service.update_task_check(test_db, today, 1, True)
    check_service.update_task_check(test_db, today, 2, True)

    assert check_service.is_day_complete(test_db, today)
