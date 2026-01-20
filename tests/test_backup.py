import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import timedelta
import json
import io

from app.services import backup as backup_service
from app.models.profile import Profile
from app.models.task import Task
from app.models.task_check import TaskCheck
from app.models.daily_status import DailyStatus
from app.core.time import get_today, get_now


def test_export_profile_data(test_db: Session, sample_tasks, sample_profiles):
    """Test exporting a single profile's data."""
    # Add some checks and daily status
    today = get_today()
    check = TaskCheck(date=today, task_id=1, user_id=1, checked=True, checked_at=get_now())
    status = DailyStatus(date=today, user_id=1, completed_at=get_now())
    test_db.add(check)
    test_db.add(status)
    test_db.commit()

    # Export profile 1
    export_data = backup_service.export_profile_data(test_db, 1)

    assert export_data is not None
    assert export_data["version"] == "1.0"
    assert "export_date" in export_data
    assert export_data["profile"]["id"] == 1
    assert export_data["profile"]["name"] == "Test Profile 1"
    assert len(export_data["tasks"]) == 3
    assert len(export_data["task_checks"]) == 1
    assert len(export_data["daily_status"]) == 1


def test_export_nonexistent_profile(test_db: Session, sample_profiles):
    """Test exporting a profile that doesn't exist."""
    export_data = backup_service.export_profile_data(test_db, 999)
    assert export_data is None


def test_export_all_profiles(test_db: Session, sample_tasks, sample_profiles):
    """Test exporting all profiles."""
    export_data = backup_service.export_all_profiles(test_db)

    assert export_data is not None
    assert export_data["version"] == "1.0"
    assert "export_date" in export_data
    assert "profiles" in export_data
    assert len(export_data["profiles"]) == 2  # We have 2 profiles from fixture


def test_validate_import_data_valid(test_db: Session, sample_tasks, sample_profiles):
    """Test validation with valid import data."""
    export_data = backup_service.export_profile_data(test_db, 1)
    is_valid, error = backup_service.validate_import_data(export_data, is_single_profile=True)

    assert is_valid is True
    assert error is None


def test_validate_import_data_missing_version():
    """Test validation with missing version field."""
    data = {"profile": {}, "tasks": [], "task_checks": [], "daily_status": []}
    is_valid, error = backup_service.validate_import_data(data, is_single_profile=True)

    assert is_valid is False
    assert "Missing 'version' field" in error


def test_validate_import_data_wrong_version():
    """Test validation with unsupported version."""
    data = {"version": "2.0", "profile": {}, "tasks": [], "task_checks": [], "daily_status": []}
    is_valid, error = backup_service.validate_import_data(data, is_single_profile=True)

    assert is_valid is False
    assert "Unsupported backup version" in error


def test_validate_import_data_missing_fields():
    """Test validation with missing required fields."""
    data = {"version": "1.0", "profile": {}}
    is_valid, error = backup_service.validate_import_data(data, is_single_profile=True)

    assert is_valid is False
    assert "Missing required field" in error


def test_validate_import_data_invalid_profile():
    """Test validation with invalid profile data."""
    data = {
        "version": "1.0",
        "profile": "invalid",  # Should be dict
        "tasks": [],
        "task_checks": [],
        "daily_status": []
    }
    is_valid, error = backup_service.validate_import_data(data, is_single_profile=True)

    assert is_valid is False
    assert "Invalid profile data" in error


def test_import_profile_data_replace_mode(test_db: Session, sample_tasks, sample_profiles):
    """Test importing profile data in replace mode."""
    # Export profile 1
    export_data = backup_service.export_profile_data(test_db, 1)

    # Modify the export data
    export_data["profile"]["name"] = "Updated Profile"
    export_data["tasks"][0]["title"] = "Updated Task"

    # Import in replace mode
    success, error = backup_service.import_profile_data(test_db, export_data, profile_id=1, mode="replace")

    assert success is True
    assert error is None

    # Verify the data was updated
    profile = test_db.query(Profile).filter(Profile.id == 1).first()
    assert profile.name == "Updated Profile"

    task = test_db.query(Task).filter(Task.id == 1).first()
    assert task.title == "Updated Task"


def test_import_profile_data_merge_mode(test_db: Session, sample_tasks, sample_profiles):
    """Test importing profile data in merge mode."""
    # Create initial data
    today = get_today()
    check = TaskCheck(date=today, task_id=1, user_id=1, checked=True, checked_at=get_now())
    test_db.add(check)
    test_db.commit()

    # Export profile 1
    export_data = backup_service.export_profile_data(test_db, 1)

    # Add a new task to the export
    new_task = {
        "id": 10,
        "title": "New Task",
        "sort_order": 4,
        "is_required": False,
        "is_active": True
    }
    export_data["tasks"].append(new_task)

    # Import in merge mode
    success, error = backup_service.import_profile_data(test_db, export_data, profile_id=1, mode="merge")

    assert success is True
    assert error is None

    # Verify original task still exists
    task1 = test_db.query(Task).filter(Task.id == 1).first()
    assert task1 is not None

    # Verify new task was added
    tasks = test_db.query(Task).filter(Task.user_id == 1).all()
    assert len(tasks) == 4


def test_import_profile_data_create_new_profile(test_db: Session, sample_profiles):
    """Test importing creates a new profile if it doesn't exist."""
    export_data = {
        "version": "1.0",
        "export_date": get_now().isoformat(),
        "profile": {
            "id": 10,
            "name": "New Profile",
            "color": "#ff0000"
        },
        "tasks": [
            {
                "id": 20,
                "title": "Task 1",
                "sort_order": 1,
                "is_required": True,
                "is_active": True
            }
        ],
        "task_checks": [],
        "daily_status": []
    }

    success, error = backup_service.import_profile_data(test_db, export_data, profile_id=10, mode="replace")

    assert success is True
    assert error is None

    # Verify profile was created
    profile = test_db.query(Profile).filter(Profile.id == 10).first()
    assert profile is not None
    assert profile.name == "New Profile"

    # Verify task was created
    task = test_db.query(Task).filter(Task.user_id == 10).first()
    assert task is not None


def test_import_profile_data_invalid_mode(test_db: Session, sample_profiles):
    """Test importing with invalid mode."""
    export_data = {
        "version": "1.0",
        "export_date": get_now().isoformat(),
        "profile": {"id": 1, "name": "Test", "color": "#ff0000"},
        "tasks": [],
        "task_checks": [],
        "daily_status": []
    }

    success, error = backup_service.import_profile_data(test_db, export_data, profile_id=1, mode="invalid")

    assert success is False
    assert "Invalid import mode" in error


def test_import_all_profiles(test_db: Session, sample_profiles):
    """Test importing all profiles."""
    export_data = {
        "version": "1.0",
        "export_date": get_now().isoformat(),
        "profiles": [
            {
                "version": "1.0",
                "export_date": get_now().isoformat(),
                "profile": {"id": 20, "name": "Profile A", "color": "#ff0000"},
                "tasks": [],
                "task_checks": [],
                "daily_status": []
            },
            {
                "version": "1.0",
                "export_date": get_now().isoformat(),
                "profile": {"id": 21, "name": "Profile B", "color": "#00ff00"},
                "tasks": [],
                "task_checks": [],
                "daily_status": []
            }
        ]
    }

    success, error = backup_service.import_all_profiles(test_db, export_data, mode="replace")

    assert success is True
    assert error is None

    # Verify profiles were created
    profile_a = test_db.query(Profile).filter(Profile.id == 20).first()
    profile_b = test_db.query(Profile).filter(Profile.id == 21).first()
    assert profile_a is not None
    assert profile_b is not None


def test_api_export_profile(client: TestClient, sample_tasks, sample_profiles):
    """Test API endpoint for exporting a profile."""
    response = client.get("/api/profiles/1/export")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert "attachment" in response.headers.get("content-disposition", "")

    data = response.json()
    assert data["version"] == "1.0"
    assert data["profile"]["id"] == 1
    assert "tasks" in data
    assert "task_checks" in data
    assert "daily_status" in data


def test_api_export_nonexistent_profile(client: TestClient, sample_profiles):
    """Test API endpoint for exporting a nonexistent profile."""
    response = client.get("/api/profiles/999/export")
    assert response.status_code == 404


def test_api_export_all_profiles(client: TestClient, sample_profiles):
    """Test API endpoint for exporting all profiles."""
    response = client.get("/api/profiles/export/all")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"

    data = response.json()
    assert data["version"] == "1.0"
    assert "profiles" in data
    assert len(data["profiles"]) >= 1


def test_api_import_profile_replace(client: TestClient, test_db: Session, sample_tasks, sample_profiles):
    """Test API endpoint for importing a profile in replace mode."""
    # Export profile 1 first
    export_response = client.get("/api/profiles/1/export")
    export_data = export_response.json()

    # Modify data
    export_data["profile"]["name"] = "Imported Profile"
    export_data["tasks"][0]["title"] = "Imported Task"

    # Create file-like object
    json_bytes = json.dumps(export_data).encode('utf-8')
    files = {"file": ("backup.json", io.BytesIO(json_bytes), "application/json")}
    data = {"mode": "replace"}

    # Import
    response = client.post("/api/profiles/1/import", files=files, data=data)

    assert response.status_code == 200
    result = response.json()
    assert "successfully" in result["message"]

    # Verify import
    profile = test_db.query(Profile).filter(Profile.id == 1).first()
    assert profile.name == "Imported Profile"


def test_api_import_profile_merge(client: TestClient, test_db: Session, sample_tasks, sample_profiles):
    """Test API endpoint for importing a profile in merge mode."""
    # Export profile 1
    export_response = client.get("/api/profiles/1/export")
    export_data = export_response.json()

    # Add a new task
    export_data["tasks"].append({
        "id": 100,
        "title": "Merged Task",
        "sort_order": 10,
        "is_required": False,
        "is_active": True
    })

    # Create file-like object
    json_bytes = json.dumps(export_data).encode('utf-8')
    files = {"file": ("backup.json", io.BytesIO(json_bytes), "application/json")}
    data = {"mode": "merge"}

    # Import
    response = client.post("/api/profiles/1/import", files=files, data=data)

    assert response.status_code == 200

    # Verify merge - original tasks should still exist
    tasks = test_db.query(Task).filter(Task.user_id == 1).all()
    assert len(tasks) >= 3  # Original 3 tasks


def test_api_import_profile_invalid_json(client: TestClient, sample_profiles):
    """Test API endpoint with invalid JSON file."""
    files = {"file": ("backup.json", io.BytesIO(b"invalid json"), "application/json")}
    data = {"mode": "replace"}

    response = client.post("/api/profiles/1/import", files=files, data=data)

    assert response.status_code == 400
    assert "Invalid JSON" in response.json()["detail"]


def test_api_import_profile_invalid_mode(client: TestClient, sample_profiles):
    """Test API endpoint with invalid import mode."""
    export_data = {"version": "1.0", "profile": {}, "tasks": [], "task_checks": [], "daily_status": []}
    json_bytes = json.dumps(export_data).encode('utf-8')
    files = {"file": ("backup.json", io.BytesIO(json_bytes), "application/json")}
    data = {"mode": "invalid"}

    response = client.post("/api/profiles/1/import", files=files, data=data)

    assert response.status_code == 400
    assert "Invalid mode" in response.json()["detail"]


def test_api_import_profile_validation_error(client: TestClient, sample_profiles):
    """Test API endpoint with invalid backup data."""
    # Missing required fields
    export_data = {"version": "1.0", "profile": {}}
    json_bytes = json.dumps(export_data).encode('utf-8')
    files = {"file": ("backup.json", io.BytesIO(json_bytes), "application/json")}
    data = {"mode": "replace"}

    response = client.post("/api/profiles/1/import", files=files, data=data)

    assert response.status_code == 400


def test_api_import_all_profiles(client: TestClient, test_db: Session, sample_profiles):
    """Test API endpoint for importing all profiles."""
    # Create export data
    export_data = {
        "version": "1.0",
        "export_date": get_now().isoformat(),
        "profiles": [
            {
                "version": "1.0",
                "export_date": get_now().isoformat(),
                "profile": {"id": 30, "name": "Bulk Profile A", "color": "#ff0000"},
                "tasks": [],
                "task_checks": [],
                "daily_status": []
            }
        ]
    }

    json_bytes = json.dumps(export_data).encode('utf-8')
    files = {"file": ("backup.json", io.BytesIO(json_bytes), "application/json")}
    data = {"mode": "replace"}

    response = client.post("/api/profiles/import/all", files=files, data=data)

    assert response.status_code == 200
    result = response.json()
    assert "successfully" in result["message"]
    assert result["profile_count"] == 1

    # Verify profile was created
    profile = test_db.query(Profile).filter(Profile.id == 30).first()
    assert profile is not None


def test_import_with_task_checks_and_daily_status(test_db: Session, sample_profiles):
    """Test importing profile with task checks and daily status."""
    today = get_today()
    yesterday = today - timedelta(days=1)

    export_data = {
        "version": "1.0",
        "export_date": get_now().isoformat(),
        "profile": {"id": 40, "name": "Test Profile", "color": "#ff0000"},
        "tasks": [
            {"id": 50, "title": "Task 1", "sort_order": 1, "is_required": True, "is_active": True}
        ],
        "task_checks": [
            {
                "date": today.isoformat(),
                "task_id": 50,
                "checked": True,
                "checked_at": get_now().isoformat()
            },
            {
                "date": yesterday.isoformat(),
                "task_id": 50,
                "checked": True,
                "checked_at": (get_now() - timedelta(days=1)).isoformat()
            }
        ],
        "daily_status": [
            {
                "date": today.isoformat(),
                "completed_at": get_now().isoformat()
            },
            {
                "date": yesterday.isoformat(),
                "completed_at": (get_now() - timedelta(days=1)).isoformat()
            }
        ]
    }

    success, error = backup_service.import_profile_data(test_db, export_data, profile_id=40, mode="replace")

    assert success is True
    assert error is None

    # Verify task checks were imported
    checks = test_db.query(TaskCheck).filter(TaskCheck.user_id == 40).all()
    assert len(checks) == 2

    # Verify daily status was imported
    statuses = test_db.query(DailyStatus).filter(DailyStatus.user_id == 40).all()
    assert len(statuses) == 2


def test_import_merge_skips_duplicates(test_db: Session, sample_tasks, sample_profiles):
    """Test that merge mode skips duplicate task checks."""
    today = get_today()

    # Create existing check
    check = TaskCheck(date=today, task_id=1, user_id=1, checked=True, checked_at=get_now())
    test_db.add(check)
    test_db.commit()

    # Export and try to import same data
    export_data = backup_service.export_profile_data(test_db, 1)

    success, error = backup_service.import_profile_data(test_db, export_data, profile_id=1, mode="merge")

    assert success is True

    # Should still only have one check for today
    checks = test_db.query(TaskCheck).filter(
        TaskCheck.user_id == 1,
        TaskCheck.date == today,
        TaskCheck.task_id == 1
    ).all()
    assert len(checks) == 1
