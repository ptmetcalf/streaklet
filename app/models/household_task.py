"""
Household Task Model

Represents shared household maintenance tasks that all profiles can view and complete.
Unlike the profile-isolated Task model, HouseholdTask has NO user_id FK - it's shared data.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.sql import func
from app.core.db import Base


class HouseholdTask(Base):
    __tablename__ = "household_tasks"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    frequency = Column(
        Enum('weekly', 'monthly', 'quarterly', 'annual', name='household_frequency'),
        nullable=False,
        index=True
    )
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<HouseholdTask(id={self.id}, title='{self.title}', frequency='{self.frequency}')>"
