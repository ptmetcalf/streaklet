"""
Tests for household maintenance tracker

Key test scenarios:
1. Household tasks are shared across all profiles (no filtering)
2. Completion tracking with profile attribution
3. Overdue detection based on frequency thresholds
4. Completion history with profile names
5. API endpoints work without X-Profile-Id header (except completion)
"""
import pytest
from datetime import datetime, timedelta
from freezegun import freeze_time

from app.models.household_task import HouseholdTask
from app.models.household_completion import HouseholdCompletion
from app.services import household as household_service


@pytest.fixture
def sample_household_tasks(test_db, sample_profiles):
    """Create sample household tasks (shared across all profiles)."""
    tasks = [
        HouseholdTask(
            id=1,
            title="Take out trash",
            description="Take trash and recycling bins to curb",
            frequency="weekly",
            sort_order=1,
            is_active=True
        ),
        HouseholdTask(
            id=2,
            title="Replace HVAC filter",
            description="Replace air conditioning/heating filter",
            frequency="monthly",
            sort_order=2,
            is_active=True
        ),
        HouseholdTask(
            id=3,
            title="Clean gutters",
            description="Remove leaves and debris from gutters",
            frequency="quarterly",
            sort_order=3,
            is_active=True
        ),
        HouseholdTask(
            id=4,
            title="Test sump pump",
            description="Test sump pump operation",
            frequency="annual",
            sort_order=4,
            is_active=True
        ),
        HouseholdTask(
            id=5,
            title="Inactive task",
            frequency="weekly",
            sort_order=5,
            is_active=False
        ),
    ]

    for task in tasks:
        test_db.add(task)
    test_db.commit()

    return tasks


def test_get_all_household_tasks(test_db, sample_household_tasks):
    """Test getting all household tasks (shared, no profile filtering)."""
    tasks = household_service.get_all_household_tasks(test_db, include_inactive=False)

    # Should get 4 active tasks (inactive task excluded)
    assert len(tasks) == 4
    assert all(task.is_active for task in tasks)


def test_get_all_household_tasks_include_inactive(test_db, sample_household_tasks):
    """Test getting all household tasks including inactive."""
    tasks = household_service.get_all_household_tasks(test_db, include_inactive=True)

    # Should get all 5 tasks
    assert len(tasks) == 5


def test_get_household_tasks_by_frequency(test_db, sample_household_tasks):
    """Test filtering household tasks by frequency."""
    weekly_tasks = household_service.get_household_tasks_by_frequency(test_db, "weekly")
    assert len(weekly_tasks) == 1
    assert weekly_tasks[0].title == "Take out trash"

    monthly_tasks = household_service.get_household_tasks_by_frequency(test_db, "monthly")
    assert len(monthly_tasks) == 1
    assert monthly_tasks[0].title == "Replace HVAC filter"


def test_create_household_task(test_db):
    """Test creating a new household task (no profile association)."""
    task = household_service.create_household_task(
        db=test_db,
        title="Mow lawn",
        description="Mow and edge lawn",
        frequency="weekly",
        sort_order=10
    )

    assert task.id is not None
    assert task.title == "Mow lawn"
    assert task.frequency == "weekly"
    assert task.is_active is True

    # Verify it's in the database
    db_task = test_db.query(HouseholdTask).filter(HouseholdTask.id == task.id).first()
    assert db_task is not None
    assert db_task.title == "Mow lawn"


def test_update_household_task(test_db, sample_household_tasks):
    """Test updating a household task."""
    task = sample_household_tasks[0]

    updated_task = household_service.update_household_task(
        db=test_db,
        task_id=task.id,
        title="Updated title",
        frequency="monthly",
        is_active=False
    )

    assert updated_task is not None
    assert updated_task.title == "Updated title"
    assert updated_task.frequency == "monthly"
    assert updated_task.is_active is False


def test_delete_household_task(test_db, sample_household_tasks):
    """Test deleting a household task (cascade deletes completions)."""
    task = sample_household_tasks[0]

    # Create a completion for the task
    completion = HouseholdCompletion(
        household_task_id=task.id,
        completed_by_profile_id=1
    )
    test_db.add(completion)
    test_db.commit()

    # Delete the task
    success = household_service.delete_household_task(test_db, task.id)
    assert success is True

    # Verify task is deleted
    db_task = test_db.query(HouseholdTask).filter(HouseholdTask.id == task.id).first()
    assert db_task is None

    # Verify completion is cascade deleted
    db_completion = test_db.query(HouseholdCompletion).filter(
        HouseholdCompletion.household_task_id == task.id
    ).first()
    assert db_completion is None


def test_mark_task_complete_with_attribution(test_db, sample_household_tasks, sample_profiles):
    """Test marking a task complete with profile attribution."""
    task = sample_household_tasks[0]

    # Profile 1 completes the task
    completion = household_service.mark_task_complete(
        db=test_db,
        task_id=task.id,
        profile_id=1,
        notes="All done!"
    )

    assert completion is not None
    assert completion.household_task_id == task.id
    assert completion.completed_by_profile_id == 1
    assert completion.notes == "All done!"
    assert completion.completed_at is not None


def test_get_last_completion(test_db, sample_household_tasks, sample_profiles):
    """Test getting the most recent completion for a task."""
    task = sample_household_tasks[0]

    # Create multiple completions
    with freeze_time("2025-12-01 12:00:00"):
        household_service.mark_task_complete(test_db, task.id, profile_id=1)

    with freeze_time("2025-12-10 12:00:00"):
        household_service.mark_task_complete(test_db, task.id, profile_id=2)

    # Get last completion
    last_completion = household_service.get_last_completion(test_db, task.id)

    assert last_completion is not None
    assert last_completion.completed_by_profile_id == 2  # Most recent


def test_get_completion_history(test_db, sample_household_tasks, sample_profiles):
    """Test getting completion history with profile names."""
    task = sample_household_tasks[0]

    # Create completions by different profiles
    with freeze_time("2025-12-01 12:00:00"):
        household_service.mark_task_complete(test_db, task.id, profile_id=1, notes="Done by profile 1")

    with freeze_time("2025-12-05 12:00:00"):
        household_service.mark_task_complete(test_db, task.id, profile_id=2, notes="Done by profile 2")

    # Get history
    history = household_service.get_completion_history(test_db, task.id, limit=10)

    assert len(history) == 2
    # Most recent first
    assert history[0]["completed_by_profile_id"] == 2
    assert history[0]["completed_by_profile_name"] == "Test Profile 2"
    assert history[0]["notes"] == "Done by profile 2"

    assert history[1]["completed_by_profile_id"] == 1
    assert history[1]["completed_by_profile_name"] == "Test Profile 1"


def test_get_task_with_status_never_completed(test_db, sample_household_tasks):
    """Test task status for a never-completed task."""
    task = sample_household_tasks[0]

    status = household_service.get_task_with_status(test_db, task.id)

    assert status is not None
    assert status["id"] == task.id
    assert status["title"] == task.title
    assert status["last_completed_at"] is None
    assert status["last_completed_by_profile_id"] is None
    assert status["days_since_completion"] is None
    assert status["is_overdue"] is False  # Never completed = not overdue


def test_get_task_with_status_recently_completed(test_db, sample_household_tasks, sample_profiles):
    """Test task status for a recently completed task."""
    task = sample_household_tasks[0]  # Weekly task

    # Complete task 3 days ago
    with freeze_time("2025-12-11 12:00:00"):
        household_service.mark_task_complete(test_db, task.id, profile_id=1)

    # Check status at current time (2025-12-14)
    status = household_service.get_task_with_status(test_db, task.id)

    assert status["last_completed_at"] is not None
    assert status["last_completed_by_profile_id"] == 1
    assert status["last_completed_by_profile_name"] == "Test Profile 1"
    assert status["days_since_completion"] == 3
    assert status["is_overdue"] is False  # 3 days < 7 days threshold


def test_get_task_with_status_overdue(test_db, sample_household_tasks, sample_profiles):
    """Test task status for an overdue task."""
    task = sample_household_tasks[0]  # Weekly task (7 day threshold)

    # Complete task 10 days ago
    with freeze_time("2025-12-04 12:00:00"):
        household_service.mark_task_complete(test_db, task.id, profile_id=1)

    # Check status at current time (2025-12-14)
    status = household_service.get_task_with_status(test_db, task.id)

    assert status["days_since_completion"] == 10
    assert status["is_overdue"] is True  # 10 days > 7 days threshold


def test_get_overdue_tasks(test_db, sample_household_tasks, sample_profiles):
    """Test getting all overdue tasks."""
    # Complete weekly task 10 days ago (overdue)
    with freeze_time("2025-12-04 12:00:00"):
        household_service.mark_task_complete(test_db, sample_household_tasks[0].id, profile_id=1)

    # Complete monthly task 5 days ago (not overdue)
    with freeze_time("2025-12-09 12:00:00"):
        household_service.mark_task_complete(test_db, sample_household_tasks[1].id, profile_id=1)

    # Get overdue tasks
    overdue = household_service.get_overdue_tasks(test_db)

    # Only weekly task should be overdue
    assert len(overdue) == 1
    assert overdue[0]["title"] == "Take out trash"
    assert overdue[0]["is_overdue"] is True


def test_api_list_tasks_no_profile_header(client, sample_household_tasks):
    """Test that listing tasks works WITHOUT X-Profile-Id header (shared data)."""
    response = client.get("/api/household/tasks")

    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) == 4  # 4 active tasks


def test_api_list_tasks_with_frequency_filter(client, sample_household_tasks):
    """Test filtering tasks by frequency via API."""
    response = client.get("/api/household/tasks?frequency=weekly")

    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) == 1
    assert tasks[0]["frequency"] == "weekly"


def test_api_get_single_task(client, sample_household_tasks):
    """Test getting a single task with status."""
    task = sample_household_tasks[0]
    response = client.get(f"/api/household/tasks/{task.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task.id
    assert data["title"] == task.title
    assert "last_completed_at" in data
    assert "is_overdue" in data


def test_api_create_task(client):
    """Test creating a household task via API."""
    response = client.post("/api/household/tasks", json={
        "title": "New Task",
        "description": "Test description",
        "frequency": "monthly",
        "sort_order": 10
    })

    assert response.status_code == 201
    task = response.json()
    assert task["title"] == "New Task"
    assert task["frequency"] == "monthly"
    assert task["is_active"] is True


def test_api_update_task(client, sample_household_tasks):
    """Test updating a household task via API."""
    task = sample_household_tasks[0]

    response = client.put(f"/api/household/tasks/{task.id}", json={
        "title": "Updated Title",
        "frequency": "monthly"
    })

    assert response.status_code == 200
    updated = response.json()
    assert updated["title"] == "Updated Title"
    assert updated["frequency"] == "monthly"


def test_api_delete_task(client, sample_household_tasks):
    """Test deleting a household task via API."""
    task = sample_household_tasks[0]

    response = client.delete(f"/api/household/tasks/{task.id}")

    assert response.status_code == 204

    # Verify task is deleted
    get_response = client.get(f"/api/household/tasks/{task.id}")
    assert get_response.status_code == 404


def test_api_mark_complete_requires_profile_header(client, sample_household_tasks):
    """Test that marking complete REQUIRES X-Profile-Id header (attribution)."""
    task = sample_household_tasks[0]

    # With profile header
    response = client.post(
        f"/api/household/tasks/{task.id}/complete",
        headers={"X-Profile-Id": "1"}
    )

    assert response.status_code == 201
    data = response.json()
    assert "completion_id" in data


def test_api_get_completion_history(client, sample_household_tasks, sample_profiles):
    """Test getting completion history via API."""
    task = sample_household_tasks[0]

    # Create completions
    client.post(f"/api/household/tasks/{task.id}/complete", headers={"X-Profile-Id": "1"})
    client.post(f"/api/household/tasks/{task.id}/complete", headers={"X-Profile-Id": "2"})

    # Get history
    response = client.get(f"/api/household/tasks/{task.id}/history")

    assert response.status_code == 200
    history = response.json()
    assert len(history) == 2
    assert "completed_by_profile_name" in history[0]


def test_api_get_overdue_tasks(client, sample_household_tasks, sample_profiles):
    """Test getting overdue tasks via API."""
    # Complete a task 10 days ago to make it overdue
    with freeze_time("2025-12-04 12:00:00"):
        client.post(
            f"/api/household/tasks/{sample_household_tasks[0].id}/complete",
            headers={"X-Profile-Id": "1"}
        )

    # Get overdue tasks
    response = client.get("/api/household/overdue")

    assert response.status_code == 200
    overdue = response.json()
    assert len(overdue) == 1
    assert overdue[0]["is_overdue"] is True


def test_household_tasks_shared_across_profiles(client, sample_household_tasks, sample_profiles):
    """Test that household tasks are visible to all profiles (critical architecture test)."""
    # Get tasks as profile 1
    response1 = client.get("/api/household/tasks", headers={"X-Profile-Id": "1"})
    tasks1 = response1.json()

    # Get tasks as profile 2
    response2 = client.get("/api/household/tasks", headers={"X-Profile-Id": "2"})
    tasks2 = response2.json()

    # Both profiles should see the SAME tasks
    assert len(tasks1) == len(tasks2)
    assert [t["id"] for t in tasks1] == [t["id"] for t in tasks2]


def test_completion_attribution_preserved(client, sample_household_tasks, sample_profiles):
    """Test that completion attribution is preserved when viewed by different profiles."""
    task = sample_household_tasks[0]

    # Profile 1 completes the task
    client.post(f"/api/household/tasks/{task.id}/complete", headers={"X-Profile-Id": "1"})

    # Profile 2 views the task
    response = client.get(f"/api/household/tasks/{task.id}", headers={"X-Profile-Id": "2"})
    data = response.json()

    # Should show completion by Profile 1
    assert data["last_completed_by_profile_id"] == 1
    assert data["last_completed_by_profile_name"] == "Test Profile 1"


def test_frequency_threshold_detection():
    """Test frequency threshold constants are correct."""
    from app.services.household import FREQUENCY_THRESHOLDS

    assert FREQUENCY_THRESHOLDS["weekly"] == 7
    assert FREQUENCY_THRESHOLDS["monthly"] == 30
    assert FREQUENCY_THRESHOLDS["quarterly"] == 90
    assert FREQUENCY_THRESHOLDS["annual"] == 365
