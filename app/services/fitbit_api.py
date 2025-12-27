"""
Fitbit API client service.

Handles fetching data from Fitbit REST API:
- Activity summary (steps, distance, floors, calories, active minutes)
- Sleep summary (sleep minutes, sleep score)
- Heart rate summary (resting heart rate)
"""
import httpx
from datetime import date
from typing import Dict, Optional
from sqlalchemy.orm import Session

from app.models.fitbit_connection import FitbitConnection
from app.services.fitbit_oauth import ensure_valid_token, decrypt_token


# Fitbit API base URL
FITBIT_API_BASE = "https://api.fitbit.com"


class FitbitAPIError(Exception):
    """Exception raised when Fitbit API request fails."""
    pass


async def _make_fitbit_request(
    db: Session,
    connection: FitbitConnection,
    endpoint: str
) -> Dict:
    """
    Make authenticated request to Fitbit API.

    Automatically refreshes token if expired.

    Args:
        db: Database session
        connection: FitbitConnection with tokens
        endpoint: API endpoint path (e.g., "/1/user/-/activities/date/2025-01-15.json")

    Returns:
        JSON response as dictionary

    Raises:
        FitbitAPIError: If request fails
    """
    # Ensure token is valid (refreshes if needed)
    connection = await ensure_valid_token(db, connection)

    # Decrypt access token
    access_token = decrypt_token(connection.access_token)

    # Make request
    url = f"{FITBIT_API_BASE}{endpoint}"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)

        if response.status_code == 401:
            # Token invalid, try refreshing
            connection = await ensure_valid_token(db, connection)
            access_token = decrypt_token(connection.access_token)
            headers["Authorization"] = f"Bearer {access_token}"
            response = await client.get(url, headers=headers)

        if response.status_code == 429:
            raise FitbitAPIError("Rate limit exceeded. Please try again later.")

        if not response.is_success:
            raise FitbitAPIError(f"Fitbit API error: {response.status_code} - {response.text}")

        return response.json()


async def fetch_activity_summary(
    db: Session,
    connection: FitbitConnection,
    target_date: date
) -> Dict[str, float]:
    """
    Fetch activity summary for a specific date.

    Returns metrics:
    - steps: Daily step count
    - distance: Distance in miles (prefers tracker-only, falls back to total)
    - floors: Floors climbed
    - calories_burned: Total calories burned
    - active_minutes_legacy: Legacy active minutes (fairly + very active) for fallback

    Note: Active minutes are now fetched separately via fetch_active_zone_minutes()
    which returns the modern AZM metric. This function provides a legacy fallback.

    Args:
        db: Database session
        connection: FitbitConnection
        target_date: Date to fetch data for

    Returns:
        Dictionary of metric_type -> value
    """
    endpoint = f"/1/user/-/activities/date/{target_date.isoformat()}.json"

    try:
        data = await _make_fitbit_request(db, connection, endpoint)

        summary = data.get("summary", {})

        metrics = {}

        # Steps
        if "steps" in summary:
            metrics["steps"] = float(summary["steps"])

        # Distance - prefer "tracker" (device-only) over "total" (includes manual logs)
        # This matches what the Fitbit app displays
        distances = summary.get("distances", [])
        distance_value = None

        # First try to find "tracker" distance
        for dist in distances:
            if dist.get("activity") == "tracker":
                distance_value = dist.get("distance", 0)
                break

        # Fall back to "total" if tracker not found
        if distance_value is None:
            for dist in distances:
                if dist.get("activity") == "total":
                    distance_value = dist.get("distance", 0)
                    break

        if distance_value is not None:
            metrics["distance"] = float(distance_value)

        # Floors
        if "floors" in summary:
            metrics["floors"] = float(summary["floors"])

        # Calories
        if "caloriesOut" in summary:
            metrics["calories_burned"] = float(summary["caloriesOut"])

        # Legacy active minutes (fairly + very active) - only for fallback
        # Modern devices should use Active Zone Minutes (AZM) instead
        fairly_active = summary.get("fairlyActiveMinutes", 0)
        very_active = summary.get("veryActiveMinutes", 0)
        if fairly_active or very_active:
            metrics["active_minutes_legacy"] = float(fairly_active + very_active)

        return metrics

    except Exception as e:
        raise FitbitAPIError(f"Failed to fetch activity summary: {e}")


async def fetch_sleep_summary(
    db: Session,
    connection: FitbitConnection,
    target_date: date
) -> Dict[str, float]:
    """
    Fetch sleep summary for a specific date.

    Returns metrics:
    - sleep_minutes: Total sleep duration in minutes
    - sleep_score: Sleep efficiency (0-100) - percentage of time in bed spent asleep

    IMPORTANT: The "sleep_score" metric is actually sleep EFFICIENCY, not the
    composite Sleep Score shown in the Fitbit mobile app. The actual Sleep Score
    is proprietary and NOT available via the Fitbit Web API. Sleep efficiency
    measures what % of time in bed was spent asleep, while the app's Sleep Score
    is a composite calculation based on duration, restoration, and sleep stages.

    Args:
        db: Database session
        connection: FitbitConnection
        target_date: Date to fetch data for

    Returns:
        Dictionary of metric_type -> value
    """
    endpoint = f"/1.2/user/-/sleep/date/{target_date.isoformat()}.json"

    try:
        data = await _make_fitbit_request(db, connection, endpoint)

        metrics = {}

        # Get sleep data
        sleep_records = data.get("sleep", [])
        if not sleep_records:
            return metrics

        # Sum total sleep minutes from all sleep records for the day
        total_sleep_minutes = sum(
            record.get("minutesAsleep", 0) for record in sleep_records
        )
        if total_sleep_minutes > 0:
            metrics["sleep_minutes"] = float(total_sleep_minutes)

        # Get sleep efficiency (stored as "sleep_score" for backwards compatibility)
        # Note: This is NOT the same as the Sleep Score in the Fitbit mobile app
        for record in sleep_records:
            if record.get("isMainSleep"):
                efficiency = record.get("efficiency")
                if efficiency is not None:
                    # Efficiency = % of time in bed spent asleep (0-100)
                    metrics["sleep_score"] = float(efficiency)
                break

        return metrics

    except Exception as e:
        # Sleep data might not be available for all dates, don't raise error
        print(f"Failed to fetch sleep summary for {target_date}: {e}")
        return {}


async def fetch_heart_rate_summary(
    db: Session,
    connection: FitbitConnection,
    target_date: date
) -> Dict[str, float]:
    """
    Fetch heart rate summary for a specific date.

    Returns metrics:
    - resting_heart_rate: Resting heart rate in bpm

    Args:
        db: Database session
        connection: FitbitConnection
        target_date: Date to fetch data for

    Returns:
        Dictionary of metric_type -> value
    """
    endpoint = f"/1/user/-/activities/heart/date/{target_date.isoformat()}/1d.json"

    try:
        data = await _make_fitbit_request(db, connection, endpoint)

        metrics = {}

        # Get heart rate data
        activities_heart = data.get("activities-heart", [])
        if activities_heart:
            heart_data = activities_heart[0].get("value", {})
            resting_hr = heart_data.get("restingHeartRate")
            if resting_hr is not None:
                metrics["resting_heart_rate"] = float(resting_hr)

        return metrics

    except Exception as e:
        # Heart rate data might not be available, don't raise error
        print(f"Failed to fetch heart rate for {target_date}: {e}")
        return {}


async def fetch_active_zone_minutes(
    db: Session,
    connection: FitbitConnection,
    target_date: date
) -> Dict[str, float]:
    """
    Fetch Active Zone Minutes for a specific date.

    Returns metrics:
    - active_minutes: Total active zone minutes (heart rate based)

    Note: Active Zone Minutes (AZM) is the modern metric that replaced
    the older "fairly active + very active" calculation. AZM is heart-rate
    based and matches what the Fitbit mobile app displays.

    Falls back to legacy calculation if AZM is not available (older devices).

    Args:
        db: Database session
        connection: FitbitConnection
        target_date: Date to fetch data for

    Returns:
        Dictionary of metric_type -> value
    """
    endpoint = f"/1/user/-/activities/active-zone-minutes/date/{target_date.isoformat()}/1d.json"

    try:
        data = await _make_fitbit_request(db, connection, endpoint)

        metrics = {}

        # Get AZM data from response
        azm_data = data.get("activities-active-zone-minutes", [])
        if azm_data and len(azm_data) > 0:
            value_obj = azm_data[0].get("value", {})
            active_zone_minutes = value_obj.get("activeZoneMinutes")
            if active_zone_minutes is not None:
                metrics["active_minutes"] = float(active_zone_minutes)

        return metrics

    except Exception as e:
        # AZM not available (older devices or API error)
        print(f"Failed to fetch Active Zone Minutes for {target_date}: {e}")
        return {}


async def fetch_all_metrics(
    db: Session,
    connection: FitbitConnection,
    target_date: date
) -> Dict[str, Dict[str, any]]:
    """
    Fetch all available metrics for a date.

    Combines activity, sleep, heart rate, and active zone minutes data.

    Args:
        db: Database session
        connection: FitbitConnection
        target_date: Date to fetch data for

    Returns:
        Dictionary of metric_type -> {value, unit, metadata}
    """
    all_metrics = {}

    # Fetch activity metrics
    activity_metrics_legacy = None
    try:
        activity_metrics = await fetch_activity_summary(db, connection, target_date)

        # Save legacy active minutes for fallback
        activity_metrics_legacy = activity_metrics.pop("active_minutes_legacy", None)

        for metric_type, value in activity_metrics.items():
            unit = {
                "steps": "steps",
                "distance": "miles",
                "floors": "floors",
                "calories_burned": "calories"
            }.get(metric_type, "")

            all_metrics[metric_type] = {
                "value": value,
                "unit": unit,
                "metadata": None
            }
    except FitbitAPIError as e:
        print(f"Activity fetch failed: {e}")

    # Fetch Active Zone Minutes (modern metric)
    try:
        azm_metrics = await fetch_active_zone_minutes(db, connection, target_date)
        if "active_minutes" in azm_metrics:
            # Use modern AZM
            all_metrics["active_minutes"] = {
                "value": azm_metrics["active_minutes"],
                "unit": "minutes",
                "metadata": {"source": "active_zone_minutes"}
            }
        elif activity_metrics_legacy is not None:
            # Fallback to legacy calculation for older devices
            all_metrics["active_minutes"] = {
                "value": activity_metrics_legacy,
                "unit": "minutes",
                "metadata": {"source": "legacy_fairly_very_active"}
            }
    except Exception as e:
        # If AZM fails, use legacy
        if activity_metrics_legacy is not None:
            all_metrics["active_minutes"] = {
                "value": activity_metrics_legacy,
                "unit": "minutes",
                "metadata": {"source": "legacy_fairly_very_active"}
            }
        print(f"Active minutes fetch failed: {e}")

    # Fetch sleep metrics
    try:
        sleep_metrics = await fetch_sleep_summary(db, connection, target_date)
        for metric_type, value in sleep_metrics.items():
            unit = {
                "sleep_minutes": "minutes",
                "sleep_score": "score"
            }.get(metric_type, "")

            all_metrics[metric_type] = {
                "value": value,
                "unit": unit,
                "metadata": None
            }
    except Exception as e:
        print(f"Sleep fetch failed: {e}")

    # Fetch heart rate metrics
    try:
        hr_metrics = await fetch_heart_rate_summary(db, connection, target_date)
        for metric_type, value in hr_metrics.items():
            unit = "bpm" if metric_type == "resting_heart_rate" else ""

            all_metrics[metric_type] = {
                "value": value,
                "unit": unit,
                "metadata": None
            }
    except Exception as e:
        print(f"Heart rate fetch failed: {e}")

    return all_metrics
