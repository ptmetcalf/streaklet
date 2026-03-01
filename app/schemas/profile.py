from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional


class ProfileBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    color: str = Field(default="#3b82f6", pattern="^#[0-9A-Fa-f]{6}$")


class ProfileCreate(ProfileBase):
    pass


class ProfileUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    confetti_enabled: Optional[bool] = None
    show_shopping_list: Optional[bool] = None


class ProfileResponse(ProfileBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    confetti_enabled: bool
    show_shopping_list: bool
    created_at: datetime
    updated_at: datetime


class ProfilePreferencesResponse(BaseModel):
    confetti_enabled: bool
    show_shopping_list: bool


class ProfilePreferencesUpdate(BaseModel):
    confetti_enabled: Optional[bool] = None
    show_shopping_list: Optional[bool] = None
