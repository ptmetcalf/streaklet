"""
Pydantic schemas for household maintenance API

These schemas define the request/response models for household task operations.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Literal
from datetime import datetime, date


class HouseholdTaskBase(BaseModel):
    """Base schema for household task data."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    frequency: Literal['weekly', 'monthly', 'quarterly', 'annual', 'todo']
    due_date: Optional[date] = None  # Optional due date for to-do items
    icon: Optional[str] = None  # Material Design Icon name
    sort_order: int = 0

    # Calendar-based recurrence fields
    recurrence_day_of_week: Optional[int] = Field(None, ge=0, le=6)  # 0-6 (Mon-Sun) for weekly
    recurrence_day_of_month: Optional[int] = Field(None, ge=1, le=31)  # 1-31 for monthly
    recurrence_month: Optional[int] = Field(None, ge=1, le=12)  # 1-12 for annual/quarterly
    recurrence_day: Optional[int] = Field(None, ge=1, le=31)  # 1-31 for annual


class HouseholdTaskCreate(HouseholdTaskBase):
    """Schema for creating a new household task."""
    pass


class HouseholdTaskUpdate(BaseModel):
    """Schema for updating a household task (all fields optional)."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    frequency: Optional[Literal['weekly', 'monthly', 'quarterly', 'annual', 'todo']] = None
    due_date: Optional[date] = None
    icon: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None

    # Calendar-based recurrence fields
    recurrence_day_of_week: Optional[int] = Field(None, ge=0, le=6)
    recurrence_day_of_month: Optional[int] = Field(None, ge=1, le=31)
    recurrence_month: Optional[int] = Field(None, ge=1, le=12)
    recurrence_day: Optional[int] = Field(None, ge=1, le=31)


class HouseholdTaskResponse(HouseholdTaskBase):
    """Schema for household task responses."""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HouseholdCompletionBase(BaseModel):
    """Base schema for household completion data."""
    notes: Optional[str] = None


class HouseholdCompletionCreate(HouseholdCompletionBase):
    """Schema for creating a household completion."""
    pass


class HouseholdCompletionResponse(BaseModel):
    """Schema for household completion responses with profile info."""
    id: int
    household_task_id: int
    completed_at: datetime
    completed_by_profile_id: int
    completed_by_profile_name: str
    notes: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class HouseholdTaskWithStatus(HouseholdTaskResponse):
    """
    Extended schema with completion status information.

    Enriched with:
    - last_completed_at: When task was last completed
    - last_completed_by_profile_id: Who completed it
    - last_completed_by_profile_name: Name of who completed it
    - days_since_completion: Days since last completion
    - next_due_date: Next date when task should be completed
    - is_due: Whether task is currently due
    - is_overdue: Whether task is overdue based on frequency
    """
    last_completed_at: Optional[datetime] = None
    last_completed_by_profile_id: Optional[int] = None
    last_completed_by_profile_name: Optional[str] = None
    days_since_completion: Optional[int] = None
    next_due_date: Optional[date] = None
    is_due: bool = False
    is_overdue: bool = False

    model_config = ConfigDict(from_attributes=True)
