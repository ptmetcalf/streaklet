from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.services import tasks as task_service


def test_seed_default_tasks(test_db: Session, sample_profiles):
    """Test seeding default tasks on empty database."""
    task_service.seed_default_tasks(test_db, profile_id=1)
    tasks = task_service.get_tasks(test_db, profile_id=1)

    assert len(tasks) == 5
    assert tasks[0].title == "Walk 10,000 steps"
    assert tasks[0].is_required is True
    assert tasks[0].is_active is True
    # Verify Fitbit fields are present (may be None for non-Fitbit tasks)
    assert hasattr(tasks[0], 'fitbit_metric_type')
    assert tasks[0].fitbit_metric_type == "steps"
    assert tasks[0].fitbit_goal_value == 10000


def test_seed_default_tasks_not_duplicate(test_db: Session, sample_profiles):
    """Test that seeding doesn't duplicate tasks."""
    task_service.seed_default_tasks(test_db, profile_id=1)
    task_service.seed_default_tasks(test_db, profile_id=1)
    tasks = task_service.get_tasks(test_db, profile_id=1)

    assert len(tasks) == 5


def test_create_task(client: TestClient, sample_profiles):
    """Test creating a new task via API."""
    response = client.post("/api/tasks", json={
        "title": "New Task",
        "sort_order": 1,
        "is_required": True,
        "is_active": True
    })

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "New Task"
    assert data["is_required"] is True


def test_list_tasks(client: TestClient, sample_tasks):
    """Test listing all tasks."""
    response = client.get("/api/tasks")

    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) == 3
    assert tasks[0]["title"] == "Task 1"


def test_update_task(client: TestClient, sample_tasks):
    """Test updating a task."""
    response = client.put("/api/tasks/1", json={
        "title": "Updated Task",
        "is_required": False
    })

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Task"
    assert data["is_required"] is False


def test_delete_task(client: TestClient, sample_tasks):
    """Test deleting a task."""
    response = client.delete("/api/tasks/1")

    assert response.status_code == 204

    response = client.get("/api/tasks")
    tasks = response.json()
    assert len(tasks) == 2


def test_create_task_with_fitbit_auto_check_missing_metric_type(client: TestClient, sample_profiles):
    """Test creating task with fitbit_auto_check=True but missing metric_type."""
    response = client.post("/api/tasks", json={
        "title": "Fitbit Task",
        "sort_order": 1,
        "is_required": True,
        "is_active": True,
        "fitbit_auto_check": True,
        "fitbit_goal_value": 10000,
        "fitbit_goal_operator": ">="
    })

    assert response.status_code == 422
    assert "fitbit_metric_type is required" in response.text


def test_create_task_with_fitbit_auto_check_empty_metric_type(client: TestClient, sample_profiles):
    """Test creating task with fitbit_auto_check=True but empty metric_type."""
    response = client.post("/api/tasks", json={
        "title": "Fitbit Task",
        "sort_order": 1,
        "is_required": True,
        "is_active": True,
        "fitbit_auto_check": True,
        "fitbit_metric_type": "",
        "fitbit_goal_value": 10000,
        "fitbit_goal_operator": ">="
    })

    assert response.status_code == 422
    assert "fitbit_metric_type is required" in response.text


def test_create_task_with_fitbit_auto_check_missing_goal_value(client: TestClient, sample_profiles):
    """Test creating task with fitbit_auto_check=True but missing goal_value."""
    response = client.post("/api/tasks", json={
        "title": "Fitbit Task",
        "sort_order": 1,
        "is_required": True,
        "is_active": True,
        "fitbit_auto_check": True,
        "fitbit_metric_type": "steps",
        "fitbit_goal_operator": ">="
    })

    assert response.status_code == 422
    assert "fitbit_goal_value is required" in response.text


def test_create_task_with_fitbit_auto_check_missing_goal_operator(client: TestClient, sample_profiles):
    """Test creating task with fitbit_auto_check=True but missing goal_operator."""
    response = client.post("/api/tasks", json={
        "title": "Fitbit Task",
        "sort_order": 1,
        "is_required": True,
        "is_active": True,
        "fitbit_auto_check": True,
        "fitbit_metric_type": "steps",
        "fitbit_goal_value": 10000
    })

    assert response.status_code == 422
    assert "fitbit_goal_operator is required" in response.text


def test_create_task_with_fitbit_auto_check_all_fields_valid(client: TestClient, sample_profiles):
    """Test creating task with fitbit_auto_check=True and all required fields."""
    response = client.post("/api/tasks", json={
        "title": "Fitbit Task",
        "sort_order": 1,
        "is_required": True,
        "is_active": True,
        "fitbit_auto_check": True,
        "fitbit_metric_type": "steps",
        "fitbit_goal_value": 10000,
        "fitbit_goal_operator": ">="
    })

    assert response.status_code == 201
    data = response.json()
    assert data["fitbit_auto_check"] is True
    assert data["fitbit_metric_type"] == "steps"
    assert data["fitbit_goal_value"] == 10000
    assert data["fitbit_goal_operator"] == ">="


def test_get_task_history_with_stats(client: TestClient, test_db: Session, sample_tasks):
    """Task history endpoint returns recent entries and summary stats."""
    from app.models.task_check import TaskCheck
    from app.core.time import get_today

    today = get_today()
    checks = [
        TaskCheck(date=today, task_id=1, user_id=1, checked=True, checked_at=datetime.utcnow()),
        TaskCheck(date=today - timedelta(days=1), task_id=1, user_id=1, checked=True, checked_at=datetime.utcnow()),
        TaskCheck(date=today - timedelta(days=3), task_id=1, user_id=1, checked=True, checked_at=datetime.utcnow()),
    ]
    for check in checks:
        test_db.add(check)
    test_db.commit()

    response = client.get("/api/tasks/1/history?limit=10")

    assert response.status_code == 200
    data = response.json()

    assert data["task_id"] == 1
    assert data["task_type"] == "daily"
    assert data["stats"]["total_completions"] == 3
    assert data["stats"]["completions_last_30_days"] == 3
    assert data["stats"]["current_streak"] == 2
    assert data["stats"]["best_streak"] == 2
    assert len(data["history"]) == 3
    assert data["history"][0]["date"] == today.isoformat()


def test_get_task_history_not_found(client: TestClient, sample_tasks):
    """Task history endpoint returns 404 for missing task."""
    response = client.get("/api/tasks/999/history")
    assert response.status_code == 404
