from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text
from app.models.profile import Profile
from app.models.task import Task
from app.schemas.profile import ProfileCreate, ProfileUpdate, ProfilePreferencesUpdate
from typing import List, Optional


DEFAULT_TASKS_FOR_NEW_PROFILE = [
    {"title": "Follow a diet", "sort_order": 1, "is_required": True, "is_active": True},
    {"title": "30 minute workout", "sort_order": 2, "is_required": True, "is_active": True},
    {"title": "Read 10 pages", "sort_order": 3, "is_required": True, "is_active": True},
    {"title": "20 minutes of hobby time", "sort_order": 4, "is_required": True, "is_active": True},
    {"title": "Drink 8 glasses of water", "sort_order": 5, "is_required": False, "is_active": True},
]


def ensure_profile_preferences_columns(db: Session) -> None:
    """
    Ensure profile preference columns exist for older SQLite databases.

    This keeps startup compatible for existing installs that have not run
    Alembic migrations yet.
    """
    columns = {
        row[1]
        for row in db.execute(text("PRAGMA table_info(profiles)")).fetchall()
    }

    altered = False
    if "confetti_enabled" not in columns:
        db.execute(text(
            "ALTER TABLE profiles "
            "ADD COLUMN confetti_enabled BOOLEAN NOT NULL DEFAULT 1"
        ))
        altered = True

    if "show_shopping_list" not in columns:
        db.execute(text(
            "ALTER TABLE profiles "
            "ADD COLUMN show_shopping_list BOOLEAN NOT NULL DEFAULT 0"
        ))
        altered = True

    task_columns = {
        row[1]
        for row in db.execute(text("PRAGMA table_info(tasks)")).fetchall()
    }
    if "custom_list_id" not in task_columns:
        db.execute(text(
            "ALTER TABLE tasks "
            "ADD COLUMN custom_list_id INTEGER"
        ))
        altered = True

    custom_lists_table_exists = db.execute(text(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='custom_lists'"
    )).fetchone()
    if not custom_lists_table_exists:
        db.execute(text(
            "CREATE TABLE custom_lists ("
            "id INTEGER PRIMARY KEY, "
            "user_id INTEGER NOT NULL, "
            "name VARCHAR NOT NULL, "
            "icon VARCHAR, "
            "template_key VARCHAR, "
            "is_enabled BOOLEAN NOT NULL DEFAULT 1, "
            "sort_order INTEGER NOT NULL DEFAULT 0, "
            "created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, "
            "updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, "
            "FOREIGN KEY(user_id) REFERENCES profiles (id)"
            ")"
        ))
        db.execute(text(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_custom_lists_user_name "
            "ON custom_lists (user_id, name)"
        ))
        db.execute(text(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_custom_lists_user_template_key "
            "ON custom_lists (user_id, template_key)"
        ))
        db.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_custom_lists_user_id ON custom_lists (user_id)"
        ))
        altered = True

    if altered:
        db.commit()

    from app.services import custom_lists as custom_list_service

    profile_ids = [row[0] for row in db.execute(text("SELECT id FROM profiles")).fetchall()]
    for profile_id in profile_ids:
        custom_list_service.ensure_default_custom_lists_for_profile(db, profile_id)

    db.execute(text(
        "UPDATE tasks "
        "SET task_type='custom_list', "
        "    custom_list_id=("
        "        SELECT id FROM custom_lists "
        "        WHERE user_id = tasks.user_id AND template_key = 'shopping' "
        "        LIMIT 1"
        "    ), "
        "    is_required=0 "
        "WHERE task_type='shopping_list'"
    ))
    db.commit()


def seed_default_profile(db: Session) -> None:
    """Seed default profile if profiles table is empty."""
    ensure_profile_preferences_columns(db)

    existing = db.query(Profile).filter(Profile.id == 1).first()
    if not existing:
        profile = Profile(id=1, name="Default Profile", color="#3b82f6")
        db.add(profile)
        db.commit()

    from app.services import custom_lists as custom_list_service
    custom_list_service.ensure_default_custom_lists_for_profile(db, profile_id=1)


def seed_tasks_for_profile(db: Session, profile_id: int) -> None:
    """Create default tasks for a new profile."""
    for task_data in DEFAULT_TASKS_FOR_NEW_PROFILE:
        task = Task(**task_data, user_id=profile_id)
        db.add(task)
    db.commit()

    from app.services import custom_lists as custom_list_service
    custom_list_service.ensure_default_custom_lists_for_profile(db, profile_id)


def get_profiles(db: Session) -> List[Profile]:
    """Get all profiles."""
    return db.query(Profile).order_by(Profile.name).all()


def get_profile_by_id(db: Session, profile_id: int) -> Optional[Profile]:
    """Get a profile by ID."""
    return db.query(Profile).filter(Profile.id == profile_id).first()


def create_profile(db: Session, profile: ProfileCreate) -> Optional[Profile]:
    """Create a new profile with sample tasks."""
    try:
        db_profile = Profile(**profile.model_dump())
        db.add(db_profile)
        db.flush()  # Get the profile ID without committing yet

        # Seed default tasks for this profile
        seed_tasks_for_profile(db, db_profile.id)

        db.commit()
        db.refresh(db_profile)
        return db_profile
    except IntegrityError:
        db.rollback()
        return None  # Duplicate name


def update_profile(db: Session, profile_id: int, profile_update: ProfileUpdate) -> Optional[Profile]:
    """Update a profile."""
    db_profile = get_profile_by_id(db, profile_id)
    if not db_profile:
        return None

    update_data = profile_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_profile, key, value)

    try:
        db.commit()
        db.refresh(db_profile)
        return db_profile
    except IntegrityError:
        db.rollback()
        return None  # Duplicate name


def update_profile_preferences(
    db: Session,
    profile_id: int,
    preferences: ProfilePreferencesUpdate
) -> Optional[Profile]:
    """Update current profile UI preferences."""
    db_profile = get_profile_by_id(db, profile_id)
    if not db_profile:
        return None

    update_data = preferences.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_profile, key, value)

    db.commit()
    db.refresh(db_profile)
    return db_profile


def delete_profile(db: Session, profile_id: int) -> bool:
    """Delete a profile (cascade deletes all user data)."""
    # Prevent deletion of the last profile
    profile_count = db.query(Profile).count()
    if profile_count <= 1:
        return False

    db_profile = get_profile_by_id(db, profile_id)
    if not db_profile:
        return False

    # SQLAlchemy will handle cascade deletion via foreign keys
    db.delete(db_profile)
    db.commit()
    return True
