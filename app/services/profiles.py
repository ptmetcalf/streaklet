from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.profile import Profile
from app.models.task import Task
from app.schemas.profile import ProfileCreate, ProfileUpdate
from typing import List, Optional


DEFAULT_TASKS_FOR_NEW_PROFILE = [
    {"title": "Follow a diet", "sort_order": 1, "is_required": True, "is_active": True},
    {"title": "30 minute workout", "sort_order": 2, "is_required": True, "is_active": True},
    {"title": "Read 10 pages", "sort_order": 3, "is_required": True, "is_active": True},
    {"title": "20 minutes of hobby time", "sort_order": 4, "is_required": True, "is_active": True},
    {"title": "Drink 8 glasses of water", "sort_order": 5, "is_required": False, "is_active": True},
]


def seed_default_profile(db: Session) -> None:
    """Seed default profile if profiles table is empty."""
    existing = db.query(Profile).filter(Profile.id == 1).first()
    if not existing:
        profile = Profile(id=1, name="Default Profile", color="#3b82f6")
        db.add(profile)
        db.commit()


def seed_tasks_for_profile(db: Session, profile_id: int) -> None:
    """Create default tasks for a new profile."""
    for task_data in DEFAULT_TASKS_FOR_NEW_PROFILE:
        task = Task(**task_data, user_id=profile_id)
        db.add(task)
    db.commit()


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
