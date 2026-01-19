"""
Fitbit user preferences model.

Stores user-specific preferences for Fitbit dashboard display and goals.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Float, JSON
from sqlalchemy.orm import relationship

from app.core.db import Base


class FitbitPreferences(Base):
    """
    User preferences for Fitbit metrics display and goals.

    Allows users to customize which metrics they see and set custom goals.
    """
    __tablename__ = "fitbit_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("profiles.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)

    # Metric visibility toggles
    show_steps = Column(Boolean, default=True, nullable=False)
    show_distance = Column(Boolean, default=True, nullable=False)
    show_floors = Column(Boolean, default=True, nullable=False)
    show_calories = Column(Boolean, default=True, nullable=False)
    show_active_minutes = Column(Boolean, default=True, nullable=False)
    show_sleep = Column(Boolean, default=True, nullable=False)
    show_sleep_stages = Column(Boolean, default=True, nullable=False)
    show_heart_rate = Column(Boolean, default=True, nullable=False)
    show_hrv = Column(Boolean, default=True, nullable=False)
    show_cardio_fitness = Column(Boolean, default=True, nullable=False)
    show_breathing_rate = Column(Boolean, default=True, nullable=False)
    show_spo2 = Column(Boolean, default=True, nullable=False)
    show_temperature = Column(Boolean, default=True, nullable=False)
    show_weight = Column(Boolean, default=False, nullable=False)
    show_body_fat = Column(Boolean, default=False, nullable=False)
    show_water = Column(Boolean, default=False, nullable=False)

    # Custom goals (null = use defaults)
    goal_steps = Column(Integer, nullable=True)  # Default: 10000
    goal_active_minutes = Column(Integer, nullable=True)  # Default: 30
    goal_sleep_hours = Column(Float, nullable=True)  # Default: 8.0
    goal_water_oz = Column(Integer, nullable=True)  # Default: 64
    goal_weekly_steps = Column(Integer, nullable=True)  # Default: 70000

    # Dashboard preferences
    default_tab = Column(String, default="overview", nullable=False)  # Which tab to show first
    chart_preferences = Column(JSON, nullable=True)  # Store chart-specific settings

    # Relationship
    profile = relationship("Profile", back_populates="fitbit_preferences")
