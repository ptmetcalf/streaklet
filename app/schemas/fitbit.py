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
