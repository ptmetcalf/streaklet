from pydantic import BaseModel
from datetime import date
from typing import Optional


class StreakResponse(BaseModel):
    current_streak: int
    today_complete: bool
    last_completed_date: Optional[date]
    today_date: date
