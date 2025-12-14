from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, List


class TaskWithCheck(BaseModel):
    id: int
    title: str
    sort_order: int
    is_required: bool
    is_active: bool
    checked: bool
    checked_at: Optional[datetime]

    class Config:
        from_attributes = True


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
