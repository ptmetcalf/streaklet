import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.services import tasks as task_service
from app.schemas.task import TaskCreate


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
