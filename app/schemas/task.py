from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class TaskBase(BaseModel):
    title: str
    sort_order: int = 0
    is_required: bool = True
    is_active: bool = True


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    sort_order: Optional[int] = None
    is_required: Optional[bool] = None
    is_active: Optional[bool] = None


class TaskResponse(TaskBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
