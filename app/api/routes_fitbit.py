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
import re
from urllib.parse import quote, urlparse

from app.core.db import get_db
from app.core.profile_context import get_profile_id
from app.schemas.fitbit import (
    FitbitConnectionResponse,
    FitbitConnectResponse,
    FitbitSyncStatus,
    FitbitMetricResponse,
    FitbitDailySummary,
    FitbitPreferencesResponse,
    FitbitPreferencesUpdate
)
from app.services import fitbit_oauth, fitbit_connection, fitbit_preferences
from app.models.fitbit_metric import FitbitMetric


router = APIRouter(prefix="/api/fitbit", tags=["fitbit"])
_NOT_CONNECTED_DETAIL = "Not connected to Fitbit"

# Hardcoded safe redirect path - never modified by user input
_SETTINGS_REDIRECT_PATH = "/settings"

# In-memory state storage (use Redis in production for multi-instance deployments)
_oauth_states = {}


def _is_safe_redirect_url(url: str) -> bool:
    """
    Validate that a URL is safe for redirect (relative path only, no external domains).

    Args:
        url: URL to validate

    Returns:
        True if URL is safe (relative path with no scheme/netloc), False otherwise
    """
    # Remove backslashes (some browsers treat them as forward slashes)
    url = url.replace('\\', '')

    parsed = urlparse(url)

    # URL is safe if it has no scheme (http://, https://, etc.) and no netloc (domain)
    # This ensures it's a relative path like "/settings?param=value"
    return not parsed.scheme and not parsed.netloc


def _safe_settings_redirect(fitbit_status: str, message: str = "") -> RedirectResponse:
    """
    Create a safe redirect to settings page with Fitbit status.

    Prevents open redirect vulnerabilities by:
    - Using a hardcoded, constant redirect path (no user input in path)
    - Sanitizing and URL-encoding all query parameters
    - Limiting message length and character set
    - Validating final URL is a relative path (no external domain)

    Args:
        fitbit_status: Status to pass (e.g., "connected", "error")
        message: Optional message to include (will be sanitized and URL-encoded)

    Returns:
        RedirectResponse to /settings with safe query parameters

    Raises:
        ValueError: If constructed URL is not safe for redirect
    """
    # URL-encode the status to prevent injection
    safe_status = quote(fitbit_status, safe="")

    # Build query string safely
    query_params = f"fitbit={safe_status}"

    if message:
        # Sanitize message: restrict to safe character set, limit length and URL-encode
        raw_message = str(message)
        # Allow only alphanumerics and a small set of safe punctuation/whitespace
        normalized_message = re.sub(r"[^a-zA-Z0-9 _\-.]", "", raw_message)
        trimmed_message = normalized_message[:200]
        safe_message = quote(trimmed_message, safe="")
        query_params = f"{query_params}&message={safe_message}"

    # Construct URL with hardcoded path constant
    redirect_url = f"{_SETTINGS_REDIRECT_PATH}?{query_params}"

    # Validate URL is safe before redirecting
    if not _is_safe_redirect_url(redirect_url):
        # This should never happen with our hardcoded path, but check anyway
        raise ValueError(f"Unsafe redirect URL detected: {redirect_url}")

    return RedirectResponse(url=redirect_url)


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
        # Map raw error to a limited set of known-safe OAuth error codes
        known_errors = {
            "access_denied",
            "invalid_request",
            "invalid_client",
            "invalid_grant",
            "unauthorized_client",
            "unsupported_grant_type",
            "server_error",
        }
        safe_error = error if error in known_errors else "oauth_error"
        return _safe_settings_redirect("error", safe_error)

    # Validate required parameters
    if not code or not state:
        return _safe_settings_redirect("error", "missing_parameters")

    # Validate state token (CSRF protection)
    profile_id = _oauth_states.pop(state, None)
    if profile_id is None:
        return _safe_settings_redirect("error", "invalid_state")

    # Exchange code for tokens
    try:
        await fitbit_oauth.exchange_code_for_tokens(db, code, profile_id)
        return _safe_settings_redirect("connected")
    except Exception as e:
        return _safe_settings_redirect("error", str(e))


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
    await fitbit_connection.delete_connection(db, profile_id)
    return None


@router.post("/sync")
async def manual_sync(
    days: Optional[int] = Query(None, ge=1, le=30, description="Days of history to sync"),
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
        raise HTTPException(status_code=404, detail=_NOT_CONNECTED_DETAIL)

    try:
        # Sync recent data or bounded historical range
        if days:
            result = await fitbit_sync.sync_profile_historical(db, profile_id, days=days)
        else:
            result = await fitbit_sync.sync_profile_smart(db, profile_id)
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
        raise HTTPException(status_code=404, detail=_NOT_CONNECTED_DETAIL)

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
    connection = fitbit_connection.get_connection(db, profile_id)
    if not connection:
        raise HTTPException(status_code=404, detail=_NOT_CONNECTED_DETAIL)

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


@router.get("/daily-summary")
def get_daily_summary(
    date: date = Query(..., description="Date to get metrics for"),
    db: Session = Depends(get_db),
    profile_id: int = Depends(get_profile_id)
):
    """
    Get all Fitbit metrics for a specific date.

    Returns metrics grouped by type with value, unit, and synced_at.
    """
    connection = fitbit_connection.get_connection(db, profile_id)
    if not connection:
        raise HTTPException(status_code=404, detail=_NOT_CONNECTED_DETAIL)

    metrics = db.query(FitbitMetric).filter(
        FitbitMetric.user_id == profile_id,
        FitbitMetric.date == date
    ).all()

    metrics_dict = {
        m.metric_type: {
            "value": m.value,
            "unit": m.unit,
            "synced_at": m.synced_at.isoformat() if m.synced_at else None
        }
        for m in metrics
    }

    return {"date": date.isoformat(), "metrics": metrics_dict}


@router.get("/metrics/history")
def get_metrics_history(
    start_date: date = Query(..., description="Start date (inclusive)"),
    end_date: date = Query(..., description="End date (inclusive)"),
    metric_types: Optional[str] = Query(None, description="Comma-separated list of metric types to include"),
    db: Session = Depends(get_db),
    profile_id: int = Depends(get_profile_id)
):
    """
    Get historical Fitbit metrics for a date range.

    Returns metrics organized by date and metric type for charting.
    """
    connection = fitbit_connection.get_connection(db, profile_id)
    if not connection:
        raise HTTPException(status_code=404, detail=_NOT_CONNECTED_DETAIL)

    # Build query
    query = db.query(FitbitMetric).filter(
        FitbitMetric.user_id == profile_id,
        FitbitMetric.date >= start_date,
        FitbitMetric.date <= end_date
    )

    # Filter by metric types if specified
    if metric_types:
        types_list = [t.strip() for t in metric_types.split(',')]
        query = query.filter(FitbitMetric.metric_type.in_(types_list))

    metrics = query.order_by(FitbitMetric.date, FitbitMetric.metric_type).all()

    # Organize data by metric type
    data_by_type = {}
    for metric in metrics:
        if metric.metric_type not in data_by_type:
            data_by_type[metric.metric_type] = []
        data_by_type[metric.metric_type].append({
            "date": metric.date.isoformat(),
            "value": metric.value,
            "unit": metric.unit
        })

    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "metrics": data_by_type
    }


@router.get("/preferences", response_model=FitbitPreferencesResponse)
def get_preferences(
    db: Session = Depends(get_db),
    profile_id: int = Depends(get_profile_id)
):
    """
    Get Fitbit display preferences for current profile.

    Returns preferences for metric visibility, custom goals, and dashboard settings.
    Creates default preferences if they don't exist.
    """
    prefs = fitbit_preferences.get_preferences(db, profile_id)
    return prefs


@router.put("/preferences", response_model=FitbitPreferencesResponse)
def update_preferences(
    preferences: FitbitPreferencesUpdate,
    db: Session = Depends(get_db),
    profile_id: int = Depends(get_profile_id)
):
    """
    Update Fitbit preferences for current profile.

    Allows customization of:
    - Which metrics to show/hide in dashboard
    - Custom goal values (steps, sleep, etc.)
    - Default tab preference
    """
    prefs = fitbit_preferences.update_preferences(db, profile_id, preferences)
    return prefs


@router.post("/preferences/reset", response_model=FitbitPreferencesResponse)
def reset_preferences(
    db: Session = Depends(get_db),
    profile_id: int = Depends(get_profile_id)
):
    """
    Reset Fitbit preferences to defaults.

    Resets all visibility toggles, goals, and dashboard settings.
    """
    prefs = fitbit_preferences.reset_preferences(db, profile_id)
    return prefs


@router.get("/preferences/visible-metrics")
def get_visible_metrics(
    db: Session = Depends(get_db),
    profile_id: int = Depends(get_profile_id)
):
    """
    Get list of visible metrics for current profile.

    Returns a simple map of metric names to visibility status.
    Used by frontend to filter which metrics to display.
    """
    return fitbit_preferences.get_visible_metrics(db, profile_id)


@router.get("/preferences/goals")
def get_goals(
    db: Session = Depends(get_db),
    profile_id: int = Depends(get_profile_id)
):
    """
    Get goal values for current profile.

    Returns custom goals or defaults for steps, sleep, active minutes, etc.
    """
    return fitbit_preferences.get_goals(db, profile_id)
