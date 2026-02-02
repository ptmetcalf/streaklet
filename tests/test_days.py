from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import timedelta, datetime, date
from app.models.daily_status import DailyStatus
from app.services import checks as check_service
from app.core.time import get_today


def test_get_today_info_basic(client: TestClient, sample_tasks):
    """Test getting today's info with basic tasks."""
    response = client.get("/api/days/today", cookies={"profile_id": "1"})

    assert response.status_code == 200
    data = response.json()

    assert "date" in data
    assert "tasks" in data
    assert "all_required_complete" in data
    assert "completed_at" in data
    assert "streak" in data

    # Should have 3 tasks
    assert len(data["tasks"]) == 3

    # Check streak structure
    assert "current_streak" in data["streak"]
    assert "today_complete" in data["streak"]
    assert "last_completed_date" in data["streak"]

    # Initially nothing is complete
    assert data["all_required_complete"] is False
    assert data["completed_at"] is None
    assert data["streak"]["current_streak"] == 0


def test_get_today_info_with_checks(client: TestClient, test_db: Session, sample_tasks):
    """Test getting today's info when some tasks are checked."""
    today = get_today()

    # Check one task
    check_service.ensure_checks_exist_for_date(test_db, today, profile_id=1)
    check_service.update_task_check(test_db, today, 1, True, profile_id=1)

    response = client.get("/api/days/today", cookies={"profile_id": "1"})

    assert response.status_code == 200
    data = response.json()

    # First task should be checked
    task1 = next(t for t in data["tasks"] if t["id"] == 1)
    assert task1["checked"] is True
    assert task1["checked_at"] is not None

    # Other tasks should not be checked
    task2 = next(t for t in data["tasks"] if t["id"] == 2)
    assert task2["checked"] is False

    # Not all required complete yet (need both task 1 and 2)
    assert data["all_required_complete"] is False


def test_get_today_info_all_complete(client: TestClient, test_db: Session, sample_tasks):
    """Test getting today's info when all required tasks are complete."""
    today = get_today()

    # Check both required tasks
    check_service.ensure_checks_exist_for_date(test_db, today, profile_id=1)
    check_service.update_task_check(test_db, today, 1, True, profile_id=1)
    check_service.update_task_check(test_db, today, 2, True, profile_id=1)

    response = client.get("/api/days/today", cookies={"profile_id": "1"})

    assert response.status_code == 200
    data = response.json()

    # All required tasks should be complete
    assert data["all_required_complete"] is True
    assert data["completed_at"] is not None

    # Streak should include today
    assert data["streak"]["current_streak"] == 1
    assert data["streak"]["today_complete"] is True


def test_get_today_info_with_streak(client: TestClient, test_db: Session, sample_tasks):
    """Test getting today's info with an existing streak."""
    today = get_today()
    yesterday = today - timedelta(days=1)

    # Complete yesterday
    daily_status = DailyStatus(
        date=yesterday,
        user_id=1,
        completed_at=datetime(yesterday.year, yesterday.month, yesterday.day, 20, 0)
    )
    test_db.add(daily_status)
    test_db.commit()

    # Complete today
    check_service.ensure_checks_exist_for_date(test_db, today, profile_id=1)
    check_service.update_task_check(test_db, today, 1, True, profile_id=1)
    check_service.update_task_check(test_db, today, 2, True, profile_id=1)

    response = client.get("/api/days/today", cookies={"profile_id": "1"})

    assert response.status_code == 200
    data = response.json()

    # Should have a 2-day streak
    assert data["streak"]["current_streak"] == 2
    assert data["streak"]["today_complete"] is True
    assert data["streak"]["last_completed_date"] == today.isoformat()


def test_get_today_info_different_profile(client: TestClient, test_db: Session, sample_tasks, sample_profiles):
    """Test that profile isolation works for today's info."""
    from app.models.task import Task

    # Create a task for profile 2
    task = Task(
        id=10,
        user_id=2,
        title="Profile 2 Task",
        sort_order=1,
        is_required=True,
        is_active=True,
    active_since=date(2025, 1, 1)
    )
    test_db.add(task)
    test_db.commit()

    # Get today for profile 1 - should only see profile 1 tasks
    response1 = client.get("/api/days/today", cookies={"profile_id": "1"})
    assert response1.status_code == 200
    data1 = response1.json()
    assert len(data1["tasks"]) == 3

    # Get today for profile 2 - should only see profile 2 task
    response2 = client.get("/api/days/today", cookies={"profile_id": "2"})
    assert response2.status_code == 200
    data2 = response2.json()
    assert len(data2["tasks"]) == 1
    assert data2["tasks"][0]["title"] == "Profile 2 Task"


def test_update_check_toggle_on(client: TestClient, sample_tasks):
    """Test checking a task."""
    today = get_today()

    response = client.put(
        f"/api/days/{today}/checks/1",
        json={"checked": True},
        cookies={"profile_id": "1"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data["date"] == today.isoformat()
    assert data["task_id"] == 1
    assert data["checked"] is True
    assert data["checked_at"] is not None


def test_update_check_toggle_off(client: TestClient, test_db: Session, sample_tasks):
    """Test unchecking a task."""
    today = get_today()

    # First check it
    check_service.ensure_checks_exist_for_date(test_db, today, profile_id=1)
    check_service.update_task_check(test_db, today, 1, True, profile_id=1)

    # Then uncheck it
    response = client.put(
        f"/api/days/{today}/checks/1",
        json={"checked": False},
        cookies={"profile_id": "1"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data["checked"] is False
    assert data["checked_at"] is None


def test_update_check_task_not_found(client: TestClient, sample_tasks):
    """Test checking a task that doesn't exist."""
    today = get_today()

    response = client.put(
        f"/api/days/{today}/checks/999",
        json={"checked": True},
        cookies={"profile_id": "1"}
    )

    assert response.status_code == 404
    assert "Task not found" in response.json()["detail"]


def test_update_check_wrong_profile(client: TestClient, sample_tasks, sample_profiles):
    """Test that you can't check another profile's task."""
    today = get_today()

    # Try to check task 1 (belongs to profile 1) as profile 2
    response = client.put(
        f"/api/days/{today}/checks/1",
        json={"checked": True},
        cookies={"profile_id": "2"}
    )

    assert response.status_code == 404
    assert "Task not found" in response.json()["detail"]


def test_update_check_past_date(client: TestClient, sample_tasks):
    """Test checking a task on a past date."""
    yesterday = get_today() - timedelta(days=1)

    response = client.put(
        f"/api/days/{yesterday}/checks/1",
        json={"checked": True},
        cookies={"profile_id": "1"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data["date"] == yesterday.isoformat()
    assert data["checked"] is True


def test_update_check_triggers_completion(client: TestClient, test_db: Session, sample_tasks):
    """Test that checking all required tasks marks day as complete."""
    today = get_today()

    # Check first required task
    response1 = client.put(
        f"/api/days/{today}/checks/1",
        json={"checked": True},
        cookies={"profile_id": "1"}
    )
    assert response1.status_code == 200

    # Verify day is not complete yet
    today_info = client.get("/api/days/today", cookies={"profile_id": "1"}).json()
    assert today_info["all_required_complete"] is False

    # Check second required task
    response2 = client.put(
        f"/api/days/{today}/checks/2",
        json={"checked": True},
        cookies={"profile_id": "1"}
    )
    assert response2.status_code == 200

    # Now day should be complete
    today_info = client.get("/api/days/today", cookies={"profile_id": "1"}).json()
    assert today_info["all_required_complete"] is True
    assert today_info["completed_at"] is not None


def test_update_check_default_profile(client: TestClient, sample_tasks):
    """Test that omitting X-Profile-Id defaults to profile 1."""
    today = get_today()

    # Make request without X-Profile-Id header
    response = client.put(
        f"/api/days/{today}/checks/1",
        json={"checked": True}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["checked"] is True

    # Verify it was applied to profile 1
    today_info = client.get("/api/days/today").json()
    task1 = next(t for t in today_info["tasks"] if t["id"] == 1)
    assert task1["checked"] is True


def test_get_today_info_no_active_tasks(client: TestClient, test_db: Session, sample_profiles):
    """Test getting today's info when profile has no active tasks."""
    # Profile 2 has no tasks
    response = client.get("/api/days/today", cookies={"profile_id": "2"})

    assert response.status_code == 200
    data = response.json()

    assert len(data["tasks"]) == 0
    # When there are no tasks, day is not considered complete
    # (The service returns False when no required tasks exist)
    assert data["all_required_complete"] is False
    assert data["streak"]["current_streak"] == 0


def test_today_endpoint_includes_task_streaks(client: TestClient, test_db: Session, sample_tasks):
    """Test /api/days/today returns task_streak fields."""
    today = get_today()

    # Create a 3-day streak for task 1
    for i in range(3):
        day = today - timedelta(days=i)
        check_service.ensure_checks_exist_for_date(test_db, day, profile_id=1)
        check_service.update_task_check(test_db, day, task_id=1, checked=True, profile_id=1)

    response = client.get("/api/days/today", cookies={"profile_id": "1"})

    assert response.status_code == 200
    data = response.json()

    assert "tasks" in data
    for task in data["tasks"]:
        # Verify task streak fields are present
        assert "task_streak" in task
        assert "task_last_completed" in task
        assert "task_streak_milestone" in task

    # Task 1 should have a 3-day streak
    task1 = next(t for t in data["tasks"] if t["id"] == 1)
    assert task1["task_streak"] == 3
    assert task1["task_last_completed"] == today.isoformat()
    assert task1["task_streak_milestone"] == 7  # Next milestone


def test_task_streak_different_values_per_task(client: TestClient, test_db: Session, sample_tasks):
    """Test that different tasks can have different streak values."""
    today = get_today()

    # Task 1: 5-day streak
    for i in range(5):
        day = today - timedelta(days=i)
        check_service.ensure_checks_exist_for_date(test_db, day, profile_id=1)
        check_service.update_task_check(test_db, day, task_id=1, checked=True, profile_id=1)

    # Task 2: 2-day streak
    for i in range(2):
        day = today - timedelta(days=i)
        check_service.ensure_checks_exist_for_date(test_db, day, profile_id=1)
        check_service.update_task_check(test_db, day, task_id=2, checked=True, profile_id=1)

    response = client.get("/api/days/today", cookies={"profile_id": "1"})

    assert response.status_code == 200
    data = response.json()

    task1 = next(t for t in data["tasks"] if t["id"] == 1)
    task2 = next(t for t in data["tasks"] if t["id"] == 2)
    task3 = next(t for t in data["tasks"] if t["id"] == 3)

    assert task1["task_streak"] == 5
    assert task2["task_streak"] == 2
    assert task3["task_streak"] == 0  # No checks for task 3


def test_task_streak_milestone_calculation(client: TestClient, test_db: Session, sample_tasks):
    """Test that milestone calculation works correctly."""
    today = get_today()

    # Create a 10-day streak for task 1
    for i in range(10):
        day = today - timedelta(days=i)
        check_service.ensure_checks_exist_for_date(test_db, day, profile_id=1)
        check_service.update_task_check(test_db, day, task_id=1, checked=True, profile_id=1)

    response = client.get("/api/days/today", cookies={"profile_id": "1"})

    assert response.status_code == 200
    data = response.json()

    task1 = next(t for t in data["tasks"] if t["id"] == 1)
    assert task1["task_streak"] == 10
    assert task1["task_streak_milestone"] == 14  # Next milestone after 10


def test_task_streak_zero_for_no_checks(client: TestClient, sample_tasks):
    """Test that task streak is 0 when task has no checks."""
    response = client.get("/api/days/today", cookies={"profile_id": "1"})

    assert response.status_code == 200
    data = response.json()

    # All tasks should have 0 streak initially
    for task in data["tasks"]:
        assert task["task_streak"] == 0 or task["task_streak"] is None
        assert task["task_last_completed"] is None


def test_get_specific_day_includes_task_streaks(client: TestClient, test_db: Session, sample_tasks):
    """Test /api/days/{date} endpoint also includes task streak fields."""
    today = get_today()
    yesterday = today - timedelta(days=1)

    # Create a streak for task 1
    for i in range(3):
        day = today - timedelta(days=i)
        check_service.ensure_checks_exist_for_date(test_db, day, profile_id=1)
        check_service.update_task_check(test_db, day, task_id=1, checked=True, profile_id=1)

    response = client.get(f"/api/days/{yesterday}", cookies={"profile_id": "1"})

    assert response.status_code == 200
    data = response.json()

    task1 = next(t for t in data["tasks"] if t["id"] == 1)
    assert "task_streak" in task1
    assert "task_last_completed" in task1
    assert "task_streak_milestone" in task1
    # Streak calculation should work for any date
    assert task1["task_streak"] == 3
