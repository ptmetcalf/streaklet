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
    - distance: Distance in miles
    - floors: Floors climbed
    - calories_burned: Total calories burned
    - active_minutes: Active zone minutes

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

        # Distance (convert to miles if needed)
        distances = summary.get("distances", [])
        for dist in distances:
            if dist.get("activity") == "total":
                metrics["distance"] = float(dist.get("distance", 0))
                break

        # Floors
        if "floors" in summary:
            metrics["floors"] = float(summary["floors"])

        # Calories
        if "caloriesOut" in summary:
            metrics["calories_burned"] = float(summary["caloriesOut"])

        # Active minutes (use "fairly active" + "very active")
        fairly_active = summary.get("fairlyActiveMinutes", 0)
        very_active = summary.get("veryActiveMinutes", 0)
        metrics["active_minutes"] = float(fairly_active + very_active)

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
    - sleep_score: Sleep score (0-100) if available

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

        # Get sleep score (from the main sleep record if available)
        for record in sleep_records:
            if record.get("isMainSleep"):
                efficiency = record.get("efficiency")
                if efficiency is not None:
                    # Use efficiency as sleep score (it's a 0-100 value)
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


async def fetch_all_metrics(
    db: Session,
    connection: FitbitConnection,
    target_date: date
) -> Dict[str, Dict[str, any]]:
    """
    Fetch all available metrics for a date.

    Combines activity, sleep, and heart rate data.

    Args:
        db: Database session
        connection: FitbitConnection
        target_date: Date to fetch data for

    Returns:
        Dictionary of metric_type -> {value, unit, metadata}
    """
    all_metrics = {}

    # Fetch activity metrics
    try:
        activity_metrics = await fetch_activity_summary(db, connection, target_date)
        for metric_type, value in activity_metrics.items():
            unit = {
                "steps": "steps",
                "distance": "miles",
                "floors": "floors",
                "calories_burned": "calories",
                "active_minutes": "minutes"
            }.get(metric_type, "")

            all_metrics[metric_type] = {
                "value": value,
                "unit": unit,
                "metadata": None
            }
    except FitbitAPIError as e:
        print(f"Activity fetch failed: {e}")

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
