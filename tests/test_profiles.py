import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient


def test_list_profiles(client: TestClient, sample_profiles):
    """Test listing all profiles."""
    response = client.get("/api/profiles")
    assert response.status_code == 200
    profiles = response.json()
    assert len(profiles) == 2
    assert profiles[0]["name"] == "Test Profile 1"
    assert profiles[1]["name"] == "Test Profile 2"


def test_get_profile_by_id(client: TestClient, sample_profiles):
    """Test getting a single profile by ID."""
    response = client.get("/api/profiles/1")
    assert response.status_code == 200
    profile = response.json()
    assert profile["id"] == 1
    assert profile["name"] == "Test Profile 1"
    assert profile["color"] == "#3b82f6"


def test_get_nonexistent_profile(client: TestClient, sample_profiles):
    """Test getting a profile that doesn't exist."""
    response = client.get("/api/profiles/999")
    assert response.status_code == 404


def test_create_profile(client: TestClient, test_db: Session, sample_profiles):
    """Test creating a new profile with sample tasks."""
    response = client.post("/api/profiles", json={
        "name": "New Profile",
        "color": "#ef4444"
    })
    assert response.status_code == 201
    profile = response.json()
    assert profile["name"] == "New Profile"
    assert profile["color"] == "#ef4444"
    assert "id" in profile

    # Verify sample tasks were created for this profile
    from app.models.task import Task
    tasks = test_db.query(Task).filter(Task.user_id == profile["id"]).all()
    assert len(tasks) == 5  # Should have 5 default tasks


def test_create_profile_duplicate_name(client: TestClient, sample_profiles):
    """Test creating a profile with a duplicate name."""
    response = client.post("/api/profiles", json={
        "name": "Test Profile 1",  # Duplicate
        "color": "#ef4444"
    })
    assert response.status_code == 409


def test_update_profile(client: TestClient, sample_profiles):
    """Test updating a profile."""
    response = client.put("/api/profiles/1", json={
        "name": "Updated Profile",
        "color": "#10b981"
    })
    assert response.status_code == 200
    profile = response.json()
    assert profile["name"] == "Updated Profile"
    assert profile["color"] == "#10b981"


def test_update_nonexistent_profile(client: TestClient, sample_profiles):
    """Test updating a profile that doesn't exist."""
    response = client.put("/api/profiles/999", json={
        "name": "Updated",
        "color": "#000000"
    })
    assert response.status_code == 404


def test_delete_profile(client: TestClient, sample_profiles):
    """Test deleting a profile."""
    response = client.delete("/api/profiles/2")
    assert response.status_code == 204

    # Verify profile is deleted
    response = client.get("/api/profiles/2")
    assert response.status_code == 404


def test_delete_last_profile_fails(client: TestClient, test_db: Session):
    """Test that deleting the last profile fails."""
    from app.models.profile import Profile

    # Create only one profile
    profile = Profile(id=1, name="Only Profile", color="#3b82f6")
    test_db.add(profile)
    test_db.commit()

    response = client.delete("/api/profiles/1")
    assert response.status_code == 400
    assert "last remaining profile" in response.json()["detail"].lower()


def test_profile_data_isolation(test_db: Session, sample_profiles):
    """Test that profiles have isolated data."""
    from app.models.task import Task
    from app.services import tasks as task_service
    from datetime import date

    past_date = date(2025, 1, 1)

    # Create tasks for profile 1
    task1 = Task(user_id=1, title="Profile 1 Task", sort_order=1, is_required=True, is_active=True, active_since=past_date)
    test_db.add(task1)

    # Create tasks for profile 2
    task2 = Task(user_id=2, title="Profile 2 Task", sort_order=1, is_required=True, is_active=True, active_since=past_date)
    test_db.add(task2)
    test_db.commit()

    # Query tasks for profile 1
    tasks_p1 = task_service.get_tasks(test_db, profile_id=1)
    assert len(tasks_p1) == 1
    assert tasks_p1[0].title == "Profile 1 Task"

    # Query tasks for profile 2
    tasks_p2 = task_service.get_tasks(test_db, profile_id=2)
    assert len(tasks_p2) == 1
    assert tasks_p2[0].title == "Profile 2 Task"


def test_api_with_profile_header(client: TestClient, sample_tasks):
    """Test that API endpoints accept X-Profile-Id header."""
    # Call with X-Profile-Id: 1
    response = client.get("/api/tasks", headers={"X-Profile-Id": "1"})
    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) == 3

    # Call without header - defaults to profile 1
    response = client.get("/api/tasks")
    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) == 3
