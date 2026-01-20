"""
Backup and restore service for profile data.
Handles exporting and importing profile data in JSON format.
"""

from sqlalchemy.orm import Session
from app.models.profile import Profile
from app.models.task import Task
from app.models.task_check import TaskCheck
from app.models.daily_status import DailyStatus
from datetime import datetime
from typing import Dict, Optional, Any

from app.core.time import get_now

BACKUP_VERSION = "1.0"


def export_profile_data(db: Session, profile_id: int) -> Optional[Dict[str, Any]]:
    """
    Export all data for a single profile.

    Returns a dictionary with:
    - version: backup format version
    - export_date: ISO format timestamp
    - profile: profile information
    - tasks: list of tasks
    - task_checks: list of task completion checks
    - daily_status: list of daily completion records
    """
    # Get profile
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if not profile:
        return None

    # Get tasks
    tasks = db.query(Task).filter(Task.user_id == profile_id).order_by(Task.sort_order).all()

    # Get task checks
    task_checks = db.query(TaskCheck).filter(TaskCheck.user_id == profile_id).order_by(TaskCheck.date, TaskCheck.task_id).all()

    # Get daily status
    daily_statuses = db.query(DailyStatus).filter(DailyStatus.user_id == profile_id).order_by(DailyStatus.date).all()

    # Build export data
    export_data = {
        "version": BACKUP_VERSION,
        "export_date": get_now().isoformat(),
        "profile": {
            "id": profile.id,
            "name": profile.name,
            "color": profile.color,
            "created_at": profile.created_at.isoformat() if profile.created_at else None,
            "updated_at": profile.updated_at.isoformat() if profile.updated_at else None,
        },
        "tasks": [
            {
                "id": task.id,
                "title": task.title,
                "sort_order": task.sort_order,
                "is_required": task.is_required,
                "is_active": task.is_active,
            }
            for task in tasks
        ],
        "task_checks": [
            {
                "date": check.date.isoformat(),
                "task_id": check.task_id,
                "checked": check.checked,
                "checked_at": check.checked_at.isoformat() if check.checked_at else None,
            }
            for check in task_checks
        ],
        "daily_status": [
            {
                "date": status.date.isoformat(),
                "completed_at": status.completed_at.isoformat() if status.completed_at else None,
            }
            for status in daily_statuses
        ],
    }

    return export_data


def export_all_profiles(db: Session) -> Dict[str, Any]:
    """
    Export data for all profiles.

    Returns a dictionary with:
    - version: backup format version
    - export_date: ISO format timestamp
    - profiles: list of profile data (each with same structure as export_profile_data)
    """
    profiles = db.query(Profile).order_by(Profile.id).all()

    export_data = {
        "version": BACKUP_VERSION,
        "export_date": get_now().isoformat(),
        "profiles": []
    }

    for profile in profiles:
        profile_data = export_profile_data(db, profile.id)
        if profile_data:
            export_data["profiles"].append(profile_data)

    return export_data


def validate_import_data(data: Dict[str, Any], is_single_profile: bool = True) -> tuple[bool, Optional[str]]:
    """
    Validate import data structure.

    Returns (is_valid, error_message).
    """
    # Check version
    if "version" not in data:
        return False, "Missing 'version' field"

    if data["version"] != BACKUP_VERSION:
        return False, f"Unsupported backup version: {data['version']}"

    # Check structure based on type
    if is_single_profile:
        # Single profile export
        required_fields = ["profile", "tasks", "task_checks", "daily_status"]
        for field in required_fields:
            if field not in data:
                return False, f"Missing required field: {field}"

        # Validate profile
        profile = data["profile"]
        if not isinstance(profile, dict) or "name" not in profile:
            return False, "Invalid profile data"

        # Validate lists
        if not isinstance(data["tasks"], list):
            return False, "Invalid tasks data (must be list)"
        if not isinstance(data["task_checks"], list):
            return False, "Invalid task_checks data (must be list)"
        if not isinstance(data["daily_status"], list):
            return False, "Invalid daily_status data (must be list)"
    else:
        # All profiles export
        if "profiles" not in data:
            return False, "Missing 'profiles' field"

        if not isinstance(data["profiles"], list):
            return False, "Invalid profiles data (must be list)"

        # Validate each profile
        for i, profile_data in enumerate(data["profiles"]):
            is_valid, error = validate_import_data(profile_data, is_single_profile=True)
            if not is_valid:
                return False, f"Profile {i + 1}: {error}"

    return True, None


def import_profile_data(
    db: Session,
    data: Dict[str, Any],
    profile_id: Optional[int] = None,
    mode: str = "replace"
) -> tuple[bool, Optional[str]]:
    """
    Import profile data from backup.

    Args:
        db: Database session
        data: Import data dictionary
        profile_id: Target profile ID (if None, uses ID from data)
        mode: Import mode - 'replace' (delete existing data) or 'merge' (keep existing)

    Returns (success, error_message).
    """
    # Validate data
    is_valid, error = validate_import_data(data, is_single_profile=True)
    if not is_valid:
        return False, error

    try:
        # Determine target profile ID
        target_profile_id = profile_id if profile_id is not None else data["profile"]["id"]

        # Get or create profile
        profile = db.query(Profile).filter(Profile.id == target_profile_id).first()

        if mode == "replace":
            if profile:
                # Delete existing data
                db.query(TaskCheck).filter(TaskCheck.user_id == target_profile_id).delete()
                db.query(Task).filter(Task.user_id == target_profile_id).delete()
                db.query(DailyStatus).filter(DailyStatus.user_id == target_profile_id).delete()
                db.flush()
            else:
                # Create new profile
                profile = Profile(
                    id=target_profile_id,
                    name=data["profile"]["name"],
                    color=data["profile"]["color"]
                )
                db.add(profile)
                db.flush()

            # Update profile info
            profile.name = data["profile"]["name"]
            profile.color = data["profile"]["color"]

        elif mode == "merge":
            if not profile:
                # Create new profile
                profile = Profile(
                    id=target_profile_id,
                    name=data["profile"]["name"],
                    color=data["profile"]["color"]
                )
                db.add(profile)
                db.flush()

        else:
            return False, f"Invalid import mode: {mode}"

        # Import tasks
        existing_task_ids = set()
        if mode == "merge":
            existing_tasks = db.query(Task.id).filter(Task.user_id == target_profile_id).all()
            existing_task_ids = {task.id for task in existing_tasks}

        # Map old task IDs to new task IDs (in case of ID conflicts)
        task_id_map = {}

        for task_data in data["tasks"]:
            old_task_id = task_data.get("id")

            if mode == "merge" and old_task_id in existing_task_ids:
                # Skip existing tasks in merge mode
                task_id_map[old_task_id] = old_task_id
                continue

            task = Task(
                user_id=target_profile_id,
                title=task_data["title"],
                sort_order=task_data["sort_order"],
                is_required=task_data["is_required"],
                is_active=task_data["is_active"]
            )

            # Try to use original ID if available and mode is replace
            if mode == "replace" and old_task_id:
                task.id = old_task_id

            db.add(task)
            db.flush()  # Get the new task ID

            if old_task_id:
                task_id_map[old_task_id] = task.id

        # Import task checks
        if mode == "merge":
            # In merge mode, skip existing checks
            existing_checks = db.query(TaskCheck.date, TaskCheck.task_id).filter(
                TaskCheck.user_id == target_profile_id
            ).all()
            existing_check_keys = {(check.date, check.task_id) for check in existing_checks}

        for check_data in data["task_checks"]:
            from datetime import date as date_type
            check_date = date_type.fromisoformat(check_data["date"])
            old_task_id = check_data["task_id"]
            new_task_id = task_id_map.get(old_task_id, old_task_id)

            if mode == "merge" and (check_date, new_task_id) in existing_check_keys:
                continue

            check = TaskCheck(
                date=check_date,
                task_id=new_task_id,
                user_id=target_profile_id,
                checked=check_data["checked"],
                checked_at=datetime.fromisoformat(check_data["checked_at"]) if check_data.get("checked_at") else None
            )
            db.add(check)

        # Import daily status
        if mode == "merge":
            existing_statuses = db.query(DailyStatus.date).filter(
                DailyStatus.user_id == target_profile_id
            ).all()
            existing_status_dates = {status.date for status in existing_statuses}

        for status_data in data["daily_status"]:
            from datetime import date as date_type
            status_date = date_type.fromisoformat(status_data["date"])

            if mode == "merge" and status_date in existing_status_dates:
                continue

            status = DailyStatus(
                date=status_date,
                user_id=target_profile_id,
                completed_at=datetime.fromisoformat(status_data["completed_at"]) if status_data.get("completed_at") else None
            )
            db.add(status)

        db.commit()
        return True, None

    except Exception as e:
        db.rollback()
        return False, f"Import failed: {str(e)}"


def import_all_profiles(db: Session, data: Dict[str, Any], mode: str = "replace") -> tuple[bool, Optional[str]]:
    """
    Import data for all profiles.

    Args:
        db: Database session
        data: Import data dictionary (all profiles format)
        mode: Import mode - 'replace' or 'merge'

    Returns (success, error_message).
    """
    # Validate data
    is_valid, error = validate_import_data(data, is_single_profile=False)
    if not is_valid:
        return False, error

    try:
        for profile_data in data["profiles"]:
            success, error = import_profile_data(db, profile_data, mode=mode)
            if not success:
                return False, f"Failed to import profile '{profile_data['profile']['name']}': {error}"

        return True, None

    except Exception as e:
        return False, f"Import failed: {str(e)}"
