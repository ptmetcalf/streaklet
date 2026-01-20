"""
Fitbit API client service.

Handles fetching data from Fitbit REST API:
- Activity summary (steps, distance, floors, calories, active minutes)
- Sleep summary (sleep minutes, sleep score)
- Heart rate summary (resting heart rate)
"""
import httpx
from datetime import date
from typing import Dict
from sqlalchemy.orm import Session

from app.models.fitbit_connection import FitbitConnection
from app.services.fitbit_oauth import ensure_valid_token, refresh_access_token, decrypt_token


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
            # Token invalid, force refresh and retry once
            try:
                connection = await refresh_access_token(db, connection)
            except Exception as e:
                raise FitbitAPIError(f"Token refresh failed: {e}")

            access_token = decrypt_token(connection.access_token)
            headers["Authorization"] = f"Bearer {access_token}"
            response = await client.get(url, headers=headers)

            if response.status_code == 401:
                raise FitbitAPIError("Unauthorized after token refresh; reconnect Fitbit")

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


async def fetch_hrv_summary(
    db: Session,
    connection: FitbitConnection,
    target_date: date
) -> Dict[str, float]:
    """
    Fetch Heart Rate Variability (HRV) for a specific date.

    HRV measures variation in time between heartbeats and is an indicator
    of stress, recovery, and overall cardiovascular health.

    Returns metrics:
    - hrv_rmssd: Root Mean Square of Successive Differences (primary HRV metric)
    - hrv_deep_rmssd: HRV during deep sleep

    Args:
        db: Database session
        connection: FitbitConnection
        target_date: Date to fetch data for

    Returns:
        Dictionary of metric_type -> value
    """
    endpoint = f"/1/user/-/hrv/date/{target_date.isoformat()}.json"

    try:
        data = await _make_fitbit_request(db, connection, endpoint)

        metrics = {}

        # Get HRV data
        hrv_records = data.get("hrv", [])
        if hrv_records:
            for record in hrv_records:
                # Daily HRV summary
                daily_rmssd = record.get("value", {}).get("dailyRmssd")
                if daily_rmssd is not None:
                    metrics["hrv_rmssd"] = float(daily_rmssd)

                # Deep sleep HRV
                deep_rmssd = record.get("value", {}).get("deepRmssd")
                if deep_rmssd is not None:
                    metrics["hrv_deep_rmssd"] = float(deep_rmssd)

        return metrics

    except Exception as e:
        print(f"Failed to fetch HRV for {target_date}: {e}")
        return {}


async def fetch_cardio_fitness(
    db: Session,
    connection: FitbitConnection,
    target_date: date
) -> Dict[str, float]:
    """
    Fetch Cardio Fitness Score (VO2 Max) for a specific date.

    VO2 Max estimates aerobic fitness level based on user profile and activity.

    Returns metrics:
    - cardio_fitness_score: VO2 Max estimate (ml/kg/min)

    Args:
        db: Database session
        connection: FitbitConnection
        target_date: Date to fetch data for

    Returns:
        Dictionary of metric_type -> value
    """
    endpoint = f"/1/user/-/cardioscore/date/{target_date.isoformat()}.json"

    try:
        data = await _make_fitbit_request(db, connection, endpoint)

        metrics = {}

        # Get cardio fitness data
        cardio_data = data.get("cardioScore", [])
        if cardio_data:
            for record in cardio_data:
                vo2_max = record.get("value", {}).get("vo2Max")
                if vo2_max is not None:
                    metrics["cardio_fitness_score"] = float(vo2_max)

        return metrics

    except Exception as e:
        print(f"Failed to fetch cardio fitness for {target_date}: {e}")
        return {}


async def fetch_breathing_rate(
    db: Session,
    connection: FitbitConnection,
    target_date: date
) -> Dict[str, float]:
    """
    Fetch Breathing Rate for a specific date.

    Breathing rate is measured during sleep.

    Returns metrics:
    - breathing_rate: Average breaths per minute during sleep

    Args:
        db: Database session
        connection: FitbitConnection
        target_date: Date to fetch data for

    Returns:
        Dictionary of metric_type -> value
    """
    endpoint = f"/1/user/-/br/date/{target_date.isoformat()}.json"

    try:
        data = await _make_fitbit_request(db, connection, endpoint)

        metrics = {}

        # Get breathing rate data
        br_records = data.get("br", [])
        if br_records:
            for record in br_records:
                breathing_rate = record.get("value", {}).get("breathingRate")
                if breathing_rate is not None:
                    metrics["breathing_rate"] = float(breathing_rate)

        return metrics

    except Exception as e:
        print(f"Failed to fetch breathing rate for {target_date}: {e}")
        return {}


async def fetch_spo2(
    db: Session,
    connection: FitbitConnection,
    target_date: date
) -> Dict[str, float]:
    """
    Fetch SpO2 (blood oxygen saturation) for a specific date.

    SpO2 measures oxygen levels in blood, typically measured during sleep.

    Returns metrics:
    - spo2_avg: Average SpO2 percentage
    - spo2_min: Minimum SpO2 percentage
    - spo2_max: Maximum SpO2 percentage

    Args:
        db: Database session
        connection: FitbitConnection
        target_date: Date to fetch data for

    Returns:
        Dictionary of metric_type -> value
    """
    endpoint = f"/1/user/-/spo2/date/{target_date.isoformat()}.json"

    try:
        data = await _make_fitbit_request(db, connection, endpoint)

        metrics = {}

        # Get SpO2 data
        spo2_records = data.get("dateTime")
        if spo2_records:
            value_data = spo2_records.get("value", {})

            avg = value_data.get("avg")
            if avg is not None:
                metrics["spo2_avg"] = float(avg)

            min_val = value_data.get("min")
            if min_val is not None:
                metrics["spo2_min"] = float(min_val)

            max_val = value_data.get("max")
            if max_val is not None:
                metrics["spo2_max"] = float(max_val)

        return metrics

    except Exception as e:
        print(f"Failed to fetch SpO2 for {target_date}: {e}")
        return {}


async def fetch_temperature(
    db: Session,
    connection: FitbitConnection,
    target_date: date
) -> Dict[str, float]:
    """
    Fetch skin temperature variation for a specific date.

    Temperature is measured as a variation from personal baseline during sleep.

    Returns metrics:
    - temp_skin: Skin temperature variation from baseline (°F or °C)

    Args:
        db: Database session
        connection: FitbitConnection
        target_date: Date to fetch data for

    Returns:
        Dictionary of metric_type -> value
    """
    endpoint = f"/1/user/-/temp/skin/date/{target_date.isoformat()}.json"

    try:
        data = await _make_fitbit_request(db, connection, endpoint)

        metrics = {}

        # Get temperature data
        temp_records = data.get("tempSkin", [])
        if temp_records:
            for record in temp_records:
                temp_value = record.get("value", {}).get("nightlyRelative")
                if temp_value is not None:
                    metrics["temp_skin"] = float(temp_value)

        return metrics

    except Exception as e:
        print(f"Failed to fetch temperature for {target_date}: {e}")
        return {}


async def fetch_sleep_stages(
    db: Session,
    connection: FitbitConnection,
    target_date: date
) -> Dict[str, float]:
    """
    Fetch detailed sleep stages for a specific date.

    Breaks down sleep into stages: deep, light, REM, and wake.

    Returns metrics:
    - sleep_deep_minutes: Time in deep sleep
    - sleep_light_minutes: Time in light sleep
    - sleep_rem_minutes: Time in REM sleep
    - sleep_wake_minutes: Time awake during sleep period

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

        # Get sleep stage data
        sleep_records = data.get("sleep", [])
        if not sleep_records:
            return metrics

        # Sum stages from all sleep records for the day
        total_deep = 0
        total_light = 0
        total_rem = 0
        total_wake = 0

        for record in sleep_records:
            levels = record.get("levels", {})
            summary = levels.get("summary", {})

            # Deep sleep
            deep_data = summary.get("deep", {})
            if "minutes" in deep_data:
                total_deep += deep_data["minutes"]

            # Light sleep
            light_data = summary.get("light", {})
            if "minutes" in light_data:
                total_light += light_data["minutes"]

            # REM sleep
            rem_data = summary.get("rem", {})
            if "minutes" in rem_data:
                total_rem += rem_data["minutes"]

            # Wake time
            wake_data = summary.get("wake", {})
            if "minutes" in wake_data:
                total_wake += wake_data["minutes"]

        if total_deep > 0:
            metrics["sleep_deep_minutes"] = float(total_deep)
        if total_light > 0:
            metrics["sleep_light_minutes"] = float(total_light)
        if total_rem > 0:
            metrics["sleep_rem_minutes"] = float(total_rem)
        if total_wake > 0:
            metrics["sleep_wake_minutes"] = float(total_wake)

        return metrics

    except Exception as e:
        print(f"Failed to fetch sleep stages for {target_date}: {e}")
        return {}


async def fetch_all_metrics(
    db: Session,
    connection: FitbitConnection,
    target_date: date
) -> Dict[str, Dict[str, any]]:
    """
    Fetch all available metrics for a date.

    Combines activity, sleep, heart rate, active zone minutes, and extended health metrics.

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

    # Fetch HRV metrics
    try:
        hrv_metrics = await fetch_hrv_summary(db, connection, target_date)
        for metric_type, value in hrv_metrics.items():
            all_metrics[metric_type] = {
                "value": value,
                "unit": "ms",
                "metadata": None
            }
    except Exception as e:
        print(f"HRV fetch failed: {e}")

    # Fetch Cardio Fitness (VO2 Max)
    try:
        cardio_metrics = await fetch_cardio_fitness(db, connection, target_date)
        for metric_type, value in cardio_metrics.items():
            all_metrics[metric_type] = {
                "value": value,
                "unit": "ml/kg/min",
                "metadata": None
            }
    except Exception as e:
        print(f"Cardio fitness fetch failed: {e}")

    # Fetch Breathing Rate
    try:
        br_metrics = await fetch_breathing_rate(db, connection, target_date)
        for metric_type, value in br_metrics.items():
            all_metrics[metric_type] = {
                "value": value,
                "unit": "bpm",
                "metadata": None
            }
    except Exception as e:
        print(f"Breathing rate fetch failed: {e}")

    # Fetch SpO2
    try:
        spo2_metrics = await fetch_spo2(db, connection, target_date)
        for metric_type, value in spo2_metrics.items():
            all_metrics[metric_type] = {
                "value": value,
                "unit": "%",
                "metadata": None
            }
    except Exception as e:
        print(f"SpO2 fetch failed: {e}")

    # Fetch Temperature
    try:
        temp_metrics = await fetch_temperature(db, connection, target_date)
        for metric_type, value in temp_metrics.items():
            all_metrics[metric_type] = {
                "value": value,
                "unit": "°F",
                "metadata": None
            }
    except Exception as e:
        print(f"Temperature fetch failed: {e}")

    # Fetch Sleep Stages
    try:
        stage_metrics = await fetch_sleep_stages(db, connection, target_date)
        for metric_type, value in stage_metrics.items():
            all_metrics[metric_type] = {
                "value": value,
                "unit": "minutes",
                "metadata": None
            }
    except Exception as e:
        print(f"Sleep stages fetch failed: {e}")

    return all_metrics
