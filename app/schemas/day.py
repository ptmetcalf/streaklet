from pydantic import BaseModel, ConfigDict
from datetime import date, datetime
from typing import Optional, List


class TaskWithCheck(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    sort_order: int
    is_required: bool
    is_active: bool
    checked: bool
    checked_at: Optional[datetime]

    # Fitbit fields
    fitbit_metric_type: Optional[str] = None
    fitbit_goal_value: Optional[float] = None
    fitbit_goal_operator: Optional[str] = None
    fitbit_auto_check: bool = False

    # Fitbit progress (populated if Fitbit goal configured)
    fitbit_current_value: Optional[float] = None
    fitbit_goal_met: bool = False
    fitbit_unit: Optional[str] = None


class StreakInfo(BaseModel):
    current_streak: int
    today_complete: bool
    last_completed_date: Optional[date]


class DayResponse(BaseModel):
    date: date
    tasks: List[TaskWithCheck]
    all_required_complete: bool
    completed_at: Optional[datetime]
    streak: StreakInfo
