from pydantic import BaseModel, ConfigDict, Field, model_validator
from datetime import datetime
from typing import Optional


class TaskBase(BaseModel):
    title: str
    sort_order: int = 0
    is_required: bool = True
    is_active: bool = True
    fitbit_metric_type: Optional[str] = None
    fitbit_goal_value: Optional[float] = None
    fitbit_goal_operator: Optional[str] = None
    fitbit_auto_check: bool = False

    @model_validator(mode='after')
    def validate_fitbit_fields(self):
        """Validate that if fitbit_auto_check is True, all Fitbit fields are set."""
        if self.fitbit_auto_check:
            if not self.fitbit_metric_type or self.fitbit_metric_type == "":
                raise ValueError("fitbit_metric_type is required when fitbit_auto_check is enabled")
            if self.fitbit_goal_value is None:
                raise ValueError("fitbit_goal_value is required when fitbit_auto_check is enabled")
            if not self.fitbit_goal_operator:
                raise ValueError("fitbit_goal_operator is required when fitbit_auto_check is enabled")
        return self


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    sort_order: Optional[int] = None
    is_required: Optional[bool] = None
    is_active: Optional[bool] = None
    fitbit_metric_type: Optional[str] = None
    fitbit_goal_value: Optional[float] = None
    fitbit_goal_operator: Optional[str] = None
    fitbit_auto_check: Optional[bool] = None


class TaskResponse(TaskBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
