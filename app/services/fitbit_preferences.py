"""
Fitbit preferences service.

Handles CRUD operations for user Fitbit preferences.
"""
from sqlalchemy.orm import Session
from typing import Optional

from app.models.fitbit_preferences import FitbitPreferences
from app.schemas.fitbit import FitbitPreferencesUpdate


def get_preferences(db: Session, profile_id: int) -> Optional[FitbitPreferences]:
    """
    Get Fitbit preferences for a profile.

    Creates default preferences if they don't exist.

    Args:
        db: Database session
        profile_id: Profile ID

    Returns:
        FitbitPreferences object
    """
    prefs = db.query(FitbitPreferences).filter(
        FitbitPreferences.user_id == profile_id
    ).first()

    # Create default preferences if they don't exist
    if not prefs:
        prefs = FitbitPreferences(user_id=profile_id)
        db.add(prefs)
        db.commit()
        db.refresh(prefs)

    return prefs


def update_preferences(
    db: Session,
    profile_id: int,
    preferences: FitbitPreferencesUpdate
) -> FitbitPreferences:
    """
    Update Fitbit preferences for a profile.

    Args:
        db: Database session
        profile_id: Profile ID
        preferences: Updated preferences data

    Returns:
        Updated FitbitPreferences object
    """
    prefs = get_preferences(db, profile_id)

    # Update all fields
    for key, value in preferences.model_dump(exclude_unset=True).items():
        setattr(prefs, key, value)

    db.commit()
    db.refresh(prefs)

    return prefs


def reset_preferences(db: Session, profile_id: int) -> FitbitPreferences:
    """
    Reset preferences to defaults.

    Args:
        db: Database session
        profile_id: Profile ID

    Returns:
        Reset FitbitPreferences object
    """
    prefs = get_preferences(db, profile_id)

    # Reset to defaults
    prefs.show_steps = True
    prefs.show_distance = True
    prefs.show_floors = True
    prefs.show_calories = True
    prefs.show_active_minutes = True
    prefs.show_sleep = True
    prefs.show_sleep_stages = True
    prefs.show_heart_rate = True
    prefs.show_hrv = True
    prefs.show_cardio_fitness = True
    prefs.show_breathing_rate = True
    prefs.show_spo2 = True
    prefs.show_temperature = True
    prefs.show_weight = False
    prefs.show_body_fat = False
    prefs.show_water = False

    prefs.goal_steps = None
    prefs.goal_active_minutes = None
    prefs.goal_sleep_hours = None
    prefs.goal_water_oz = None
    prefs.goal_weekly_steps = None

    prefs.default_tab = "overview"
    prefs.chart_preferences = None

    db.commit()
    db.refresh(prefs)

    return prefs


def get_visible_metrics(db: Session, profile_id: int) -> dict:
    """
    Get list of visible metrics for a profile.

    Returns a dictionary mapping metric names to visibility.

    Args:
        db: Database session
        profile_id: Profile ID

    Returns:
        Dictionary of metric_name -> bool
    """
    prefs = get_preferences(db, profile_id)

    return {
        "steps": prefs.show_steps,
        "distance": prefs.show_distance,
        "floors": prefs.show_floors,
        "calories_burned": prefs.show_calories,
        "active_minutes": prefs.show_active_minutes,
        "sleep_minutes": prefs.show_sleep,
        "sleep_stages": prefs.show_sleep_stages,
        "resting_heart_rate": prefs.show_heart_rate,
        "hrv": prefs.show_hrv,
        "cardio_fitness": prefs.show_cardio_fitness,
        "breathing_rate": prefs.show_breathing_rate,
        "spo2": prefs.show_spo2,
        "temperature": prefs.show_temperature,
        "weight": prefs.show_weight,
        "body_fat": prefs.show_body_fat,
        "water": prefs.show_water,
    }


def get_goals(db: Session, profile_id: int) -> dict:
    """
    Get custom goals or defaults for a profile.

    Args:
        db: Database session
        profile_id: Profile ID

    Returns:
        Dictionary of goal_name -> value
    """
    prefs = get_preferences(db, profile_id)

    return {
        "steps": prefs.goal_steps or 10000,
        "active_minutes": prefs.goal_active_minutes or 30,
        "sleep_hours": prefs.goal_sleep_hours or 8.0,
        "water_oz": prefs.goal_water_oz or 64,
        "weekly_steps": prefs.goal_weekly_steps or 70000,
    }
