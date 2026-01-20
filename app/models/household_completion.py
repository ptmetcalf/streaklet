"""
Household Completion Model

Tracks completion history for household tasks with profile attribution.
Records WHO completed a task and WHEN.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.core.db import Base


class HouseholdCompletion(Base):
    __tablename__ = "household_completions"

    id = Column(Integer, primary_key=True)
    household_task_id = Column(
        Integer,
        ForeignKey("household_tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    completed_at = Column(DateTime, server_default=func.now(), index=True)
    completed_by_profile_id = Column(
        Integer,
        ForeignKey("profiles.id"),
        nullable=False,
        index=True
    )
    notes = Column(String, nullable=True)

    def __repr__(self):
        return f"<HouseholdCompletion(id={self.id}, task_id={self.household_task_id}, profile_id={self.completed_by_profile_id})>"
