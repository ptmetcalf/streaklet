"""
Fitbit API routes.

Endpoints:
- OAuth flow (connect, callback)
- Connection management (status, disconnect)
- Manual sync
- Data retrieval (metrics, daily summary)
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional, List
import secrets

from app.core.db import get_db
from app.core.profile_context import get_profile_id
from app.schemas.fitbit import (
    FitbitConnectionResponse,
    FitbitConnectResponse,
    FitbitSyncStatus,
    FitbitMetricResponse,
    FitbitDailySummary
)
from app.services import fitbit_oauth, fitbit_connection
from app.models.fitbit_metric import FitbitMetric


router = APIRouter(prefix="/api/fitbit", tags=["fitbit"])


# In-memory state storage (use Redis in production for multi-instance deployments)
_oauth_states = {}


@router.get("/connect", response_model=FitbitConnectResponse)
async def initiate_connection(
    request: Request,
    profile_id: int = Depends(get_profile_id)
):
    """
    Initiate Fitbit OAuth 2.0 flow.

    Generates authorization URL and redirects user to Fitbit.
    State token is stored for CSRF protection.
    """
    # Generate state token for CSRF protection
    state = secrets.token_urlsafe(32)

    # Store state with profile_id (expires after 10 minutes in production)
    _oauth_states[state] = profile_id

    # Generate auth URL
    auth_url = fitbit_oauth.generate_auth_url(state)

    return FitbitConnectResponse(redirect_url=auth_url, state=state)


@router.get("/callback")
async def oauth_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    OAuth callback handler.

    Validates state token, exchanges code for tokens, and redirects to settings.
    """
    # Check for OAuth errors
    if error:
        return RedirectResponse(url=f"/settings?fitbit=error&message={error}")

    # Validate required parameters
    if not code or not state:
        return RedirectResponse(url="/settings?fitbit=error&message=missing_parameters")

    # Validate state token (CSRF protection)
    profile_id = _oauth_states.pop(state, None)
    if profile_id is None:
        return RedirectResponse(url="/settings?fitbit=error&message=invalid_state")

    # Exchange code for tokens
    try:
        await fitbit_oauth.exchange_code_for_tokens(db, code, profile_id)
        return RedirectResponse(url="/settings?fitbit=connected")
    except Exception as e:
        return RedirectResponse(url=f"/settings?fitbit=error&message={str(e)}")


@router.get("/connection", response_model=FitbitConnectionResponse)
def get_connection_status(
    db: Session = Depends(get_db),
    profile_id: int = Depends(get_profile_id)
):
    """
    Get Fitbit connection status for current profile.

    Returns connection info if connected, or connected=False if not.
    """
    status = fitbit_connection.get_connection_status(db, profile_id)
    return FitbitConnectionResponse(**status)


@router.delete("/connection", status_code=204)
async def disconnect_fitbit(
    db: Session = Depends(get_db),
    profile_id: int = Depends(get_profile_id)
):
    """
    Disconnect Fitbit account and delete all associated data.

    Deletes:
    - FitbitConnection record
    - All FitbitMetric records (CASCADE)
    - Resets fitbit_auto_check on tasks to False
    """
    success = await fitbit_connection.delete_connection(db, profile_id)
    if not success:
        raise HTTPException(status_code=404, detail="No Fitbit connection found")
    return None


@router.post("/sync")
async def manual_sync(
    db: Session = Depends(get_db),
    profile_id: int = Depends(get_profile_id)
):
    """
    Trigger manual Fitbit data sync for current profile.

    Syncs recent data (today + yesterday) and triggers auto-check.
    """
    from app.services import fitbit_sync

    connection = fitbit_connection.get_connection(db, profile_id)
    if not connection:
        raise HTTPException(status_code=404, detail="No Fitbit connection found")

    try:
        # Sync recent data
        result = await fitbit_sync.sync_profile_recent(db, profile_id)
        return {
            "status": "success",
            "message": "Sync completed",
            "details": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.get("/sync-status", response_model=FitbitSyncStatus)
def get_sync_status(
    db: Session = Depends(get_db),
    profile_id: int = Depends(get_profile_id)
):
    """
    Get current sync status for profile.

    Returns last sync time and status.
    """
    connection = fitbit_connection.get_connection(db, profile_id)
    if not connection:
        raise HTTPException(status_code=404, detail="No Fitbit connection found")

    return FitbitSyncStatus(
        is_syncing=False,  # TODO: Check if sync task is running
        last_sync_at=connection.last_sync_at,
        last_sync_status=connection.last_sync_status
    )


@router.get("/metrics", response_model=List[FitbitMetricResponse])
def get_metrics(
    start_date: date = Query(..., description="Start date (inclusive)"),
    end_date: date = Query(..., description="End date (inclusive)"),
    metric_types: Optional[str] = Query(None, description="Comma-separated metric types"),
    db: Session = Depends(get_db),
    profile_id: int = Depends(get_profile_id)
):
    """
    Get Fitbit metrics for date range.

    Optionally filter by metric types (e.g., "steps,sleep_minutes").
    """
    query = db.query(FitbitMetric).filter(
        FitbitMetric.user_id == profile_id,
        FitbitMetric.date >= start_date,
        FitbitMetric.date <= end_date
    )

    if metric_types:
        types = [t.strip() for t in metric_types.split(",")]
        query = query.filter(FitbitMetric.metric_type.in_(types))

    metrics = query.order_by(FitbitMetric.date.desc(), FitbitMetric.metric_type).all()

    return metrics


@router.get("/daily-summary", response_model=FitbitDailySummary)
def get_daily_summary(
    date: date = Query(..., description="Date to get metrics for"),
    db: Session = Depends(get_db),
    profile_id: int = Depends(get_profile_id)
):
    """
    Get all Fitbit metrics for a specific date.

    Returns metrics grouped by type in a dictionary.
    """
    metrics = db.query(FitbitMetric).filter(
        FitbitMetric.user_id == profile_id,
        FitbitMetric.date == date
    ).all()

    metrics_dict = {m.metric_type: m.value for m in metrics}

    return FitbitDailySummary(date=date, metrics=metrics_dict)
