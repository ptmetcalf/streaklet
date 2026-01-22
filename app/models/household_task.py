"""
Household Task Model

Represents shared household maintenance tasks that all profiles can view and complete.
Unlike the profile-isolated Task model, HouseholdTask has NO user_id FK - it's shared data.

Supports both recurring tasks (weekly/monthly/quarterly/annual) and one-time to-do items.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, Enum
from sqlalchemy.sql import func
from app.core.db import Base


class HouseholdTask(Base):
    __tablename__ = "household_tasks"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    frequency = Column(
        Enum('weekly', 'biweekly', 'monthly', 'quarterly', 'annual', 'todo', name='household_frequency'),
        nullable=False,
        index=True
    )
    due_date = Column(Date, nullable=True)  # Optional due date for to-do items
    icon = Column(String, nullable=True)  # Material Design Icon name (e.g., 'broom', 'leaf')

    # Schedule mode: 'calendar' = fixed dates/days, 'rolling' = interval from completion
    schedule_mode = Column(String, nullable=True, default='calendar')

    # Calendar-based recurrence fields
    recurrence_day_of_week = Column(Integer, nullable=True)  # 0-6 (Mon-Sun) for weekly/biweekly tasks
    recurrence_day_of_month = Column(Integer, nullable=True)  # 1-31 for monthly tasks
    recurrence_month = Column(Integer, nullable=True)  # 1-12 for annual/quarterly tasks
    recurrence_day = Column(Integer, nullable=True)  # 1-31 for annual tasks

    # For rolling mode: track next due date
    next_due_date = Column(Date, nullable=True, index=True)

    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<HouseholdTask(id={self.id}, title='{self.title}', frequency='{self.frequency}')>"
