from pydantic import BaseModel, ConfigDict, Field
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
