from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CustomListBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    icon: Optional[str] = Field(default=None, max_length=120)
    is_enabled: bool = True
    sort_order: int = 0


class CustomListCreate(CustomListBase):
    template_key: Optional[str] = Field(default=None, max_length=80)


class CustomListUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=80)
    icon: Optional[str] = Field(default=None, max_length=120)
    is_enabled: Optional[bool] = None
    sort_order: Optional[int] = None


class CustomListReorderRequest(BaseModel):
    list_ids: list[int]


class CustomListResponse(CustomListBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    template_key: Optional[str]
    created_at: datetime
    updated_at: datetime


class CustomListItemCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    icon: Optional[str] = Field(default=None, max_length=120)
