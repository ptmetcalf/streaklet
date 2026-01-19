from pydantic import BaseModel, ConfigDict
from datetime import datetime, date
from typing import Optional, Dict


class FitbitConnectionResponse(BaseModel):
    """Response schema for Fitbit connection status."""
    model_config = ConfigDict(from_attributes=True)

    connected: bool
    fitbit_user_id: Optional[str] = None
    connected_at: Optional[datetime] = None
    last_sync_at: Optional[datetime] = None
    last_sync_status: Optional[str] = None


class FitbitMetricResponse(BaseModel):
    """Response schema for a single Fitbit metric."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    date: date
    metric_type: str
    value: float
    unit: Optional[str] = None
    synced_at: datetime


class FitbitDailySummary(BaseModel):
    """Response schema for all metrics for a specific date."""
    date: date
    metrics: Dict[str, float]  # {metric_type: value}


class FitbitSyncStatus(BaseModel):
    """Response schema for sync status."""
    is_syncing: bool
    last_sync_at: Optional[datetime] = None
    last_sync_status: Optional[str] = None


class FitbitConnectResponse(BaseModel):
    """Response schema for OAuth connect initiation."""
    redirect_url: str
    state: str


class FitbitPreferencesBase(BaseModel):
    """Base schema for Fitbit preferences."""
    # Metric visibility toggles
    show_steps: bool = True
    show_distance: bool = True
    show_floors: bool = True
    show_calories: bool = True
    show_active_minutes: bool = True
    show_sleep: bool = True
    show_sleep_stages: bool = True
    show_heart_rate: bool = True
    show_hrv: bool = True
    show_cardio_fitness: bool = True
    show_breathing_rate: bool = True
    show_spo2: bool = True
    show_temperature: bool = True
    show_weight: bool = False
    show_body_fat: bool = False
    show_water: bool = False

    # Custom goals
    goal_steps: Optional[int] = None
    goal_active_minutes: Optional[int] = None
    goal_sleep_hours: Optional[float] = None
    goal_water_oz: Optional[int] = None
    goal_weekly_steps: Optional[int] = None

    # Dashboard preferences
    default_tab: str = "overview"
    chart_preferences: Optional[Dict] = None


class FitbitPreferencesCreate(FitbitPreferencesBase):
    """Schema for creating Fitbit preferences."""
    pass


class FitbitPreferencesUpdate(FitbitPreferencesBase):
    """Schema for updating Fitbit preferences."""
    pass


class FitbitPreferencesResponse(FitbitPreferencesBase):
    """Response schema for Fitbit preferences."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
