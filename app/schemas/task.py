from pydantic import BaseModel, ConfigDict, model_validator
from datetime import datetime, date
from typing import Optional, Literal, Dict, Any


class TaskBase(BaseModel):
    title: str
    icon: Optional[str] = None  # Material Design Icon name
    sort_order: int = 0
    is_required: bool = True
    is_active: bool = True

    # Task type
    task_type: Literal['daily', 'punch_list', 'scheduled'] = 'daily'

    # Active since - only counts toward completion on dates >= this
    active_since: Optional[date] = None

    # Punch list fields
    due_date: Optional[date] = None

    # Scheduled fields
    recurrence_pattern: Optional[Dict[str, Any]] = None

    # Fitbit fields
    fitbit_metric_type: Optional[str] = None
    fitbit_goal_value: Optional[float] = None
    fitbit_goal_operator: Optional[str] = None
    fitbit_auto_check: bool = False

    @model_validator(mode='after')
    def validate_task_fields(self):
        """Validate task type-specific fields."""
        # Validate Fitbit fields
        if self.fitbit_auto_check:
            if not self.fitbit_metric_type or self.fitbit_metric_type == "":
                raise ValueError("fitbit_metric_type is required when fitbit_auto_check is enabled")
            if self.fitbit_goal_value is None:
                raise ValueError("fitbit_goal_value is required when fitbit_auto_check is enabled")
            if not self.fitbit_goal_operator:
                raise ValueError("fitbit_goal_operator is required when fitbit_auto_check is enabled")

        # Validate scheduled task fields
        if self.task_type == 'scheduled':
            if not self.recurrence_pattern:
                raise ValueError("Scheduled tasks must have recurrence_pattern")

            pattern_type = self.recurrence_pattern.get('type')
            if pattern_type not in ['days', 'weekly', 'monthly']:
                raise ValueError(f"Invalid pattern type: {pattern_type}")

            interval = self.recurrence_pattern.get('interval')
            if not interval or interval < 1:
                raise ValueError("interval must be >= 1")

            # Validate type-specific fields
            if pattern_type == 'weekly' and 'day_of_week' not in self.recurrence_pattern:
                raise ValueError("weekly pattern requires day_of_week")
            if pattern_type == 'monthly' and 'day_of_month' not in self.recurrence_pattern:
                raise ValueError("monthly pattern requires day_of_month")

        return self


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    icon: Optional[str] = None
    sort_order: Optional[int] = None
    is_required: Optional[bool] = None
    is_active: Optional[bool] = None
    task_type: Optional[Literal['daily', 'punch_list', 'scheduled']] = None
    active_since: Optional[date] = None
    due_date: Optional[date] = None
    recurrence_pattern: Optional[Dict[str, Any]] = None
    fitbit_metric_type: Optional[str] = None
    fitbit_goal_value: Optional[float] = None
    fitbit_goal_operator: Optional[str] = None
    fitbit_auto_check: Optional[bool] = None


class TaskResponse(TaskBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime

    # Computed fields from model
    completed_at: Optional[datetime] = None
    archived_at: Optional[datetime] = None
    last_occurrence_date: Optional[date] = None
    next_occurrence_date: Optional[date] = None
