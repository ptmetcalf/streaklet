"""
Fitbit sync service.

Handles:
- Syncing Fitbit data for date ranges
- Upserting metrics into database
- Historical data import
- Hourly sync updates
"""
from sqlalchemy.orm import Session
from sqlalchemy.dialects.sqlite import insert
from datetime import date, timedelta
from typing import Dict, List

from app.core.time import get_today, get_now, to_timezone_aware
from app.core.config import settings
from app.models.fitbit_connection import FitbitConnection
from app.models.fitbit_metric import FitbitMetric
from app.services import fitbit_api, fitbit_connection
from app.services.fitbit_checks import evaluate_and_apply_auto_checks


async def upsert_metrics(
    db: Session,
    profile_id: int,
    target_date: date,
    metrics: Dict[str, Dict[str, any]]
) -> int:
    """
    Upsert Fitbit metrics for a date.

    Uses INSERT ... ON CONFLICT UPDATE for efficient upserts.

    Args:
        db: Database session
        profile_id: Profile ID
        target_date: Date for metrics
        metrics: Dictionary of {metric_type: {value, unit, metadata}}

    Returns:
        Number of metrics upserted
    """
    count = 0

    for metric_type, metric_data in metrics.items():
        # Prepare data for upsert
        data = {
            "user_id": profile_id,
            "date": target_date,
            "metric_type": metric_type,
            "value": metric_data["value"],
            "unit": metric_data.get("unit"),
            "extra_data": metric_data.get("extra_data"),
            "synced_at": get_now()
        }

        # Use INSERT ... ON CONFLICT UPDATE
        stmt = insert(FitbitMetric).values(**data)
        stmt = stmt.on_conflict_do_update(
            index_elements=["user_id", "date", "metric_type"],
            set_={
                "value": stmt.excluded.value,
                "unit": stmt.excluded.unit,
                "extra_data": stmt.excluded.extra_data,
                "synced_at": stmt.excluded.synced_at
            }
        )

        db.execute(stmt)
        count += 1

    db.commit()
    return count


async def sync_profile_date_range(
    db: Session,
    profile_id: int,
    start_date: date,
    end_date: date
) -> Dict:
    """
    Sync Fitbit data for a profile for a date range.

    Args:
        db: Database session
        profile_id: Profile ID
        start_date: Start date (inclusive)
        end_date: End date (inclusive)

    Returns:
        Dictionary with sync results: {success_days, error_days, total_metrics}
    """
    connection = fitbit_connection.get_connection(db, profile_id)
    if not connection:
        return {"success_days": 0, "error_days": 0, "total_metrics": 0, "error": "No connection"}

    success_days = 0
    error_days = 0
    total_metrics = 0

    # Iterate through date range
    current_date = start_date
    while current_date <= end_date:
        try:
            # Fetch all metrics for the date
            metrics = await fitbit_api.fetch_all_metrics(db, connection, current_date)

            if metrics:
                # Upsert metrics
                count = await upsert_metrics(db, profile_id, current_date, metrics)
                total_metrics += count
                success_days += 1

                # Run auto-check evaluation for this date
                await evaluate_and_apply_auto_checks(db, profile_id, current_date)
            else:
                # No metrics available (might be future date or no data)
                error_days += 1

        except Exception as e:
            print(f"Error syncing date {current_date}: {e}")
            error_days += 1

        current_date += timedelta(days=1)

    # Update connection sync status
    connection.last_sync_at = get_now()
    connection.last_sync_status = "success" if error_days == 0 else "partial"
    db.commit()

    return {
        "success_days": success_days,
        "error_days": error_days,
        "total_metrics": total_metrics
    }


async def sync_profile_recent(db: Session, profile_id: int) -> Dict:
    """
    Sync recent data (today + yesterday) for a profile.

    Used for hourly sync to catch late updates (e.g., sleep data finalized in morning).

    Args:
        db: Database session
        profile_id: Profile ID

    Returns:
        Dictionary with sync results
    """
    today = get_today()
    yesterday = today - timedelta(days=1)

    return await sync_profile_date_range(db, profile_id, yesterday, today)


async def sync_profile_smart(
    db: Session,
    profile_id: int,
    backfill_days: int = settings.fitbit_backfill_days
) -> Dict:
    """
    Sync Fitbit data with a bounded backfill window.

    - If never synced, backfill up to backfill_days (default 7).
    - If last sync is older than yesterday, backfill from last sync date
      (bounded by backfill_days).
    - Otherwise, only sync today + yesterday.
    """
    connection = fitbit_connection.get_connection(db, profile_id)
    if not connection:
        return {"success_days": 0, "error_days": 0, "total_metrics": 0, "error": "No connection"}

    today = get_today()
    yesterday = today - timedelta(days=1)
    max_backfill_start = today - timedelta(days=backfill_days - 1)

    start_date = None
    if connection.last_sync_at is None:
        start_date = max_backfill_start
    else:
        last_sync_date = to_timezone_aware(connection.last_sync_at).date()
        if last_sync_date < yesterday:
            start_date = max(last_sync_date, max_backfill_start)

    if start_date:
        return await sync_profile_date_range(db, profile_id, start_date, today)

    return await sync_profile_date_range(db, profile_id, yesterday, today)


async def sync_profile_historical(db: Session, profile_id: int, days: int = 30) -> Dict:
    """
    Sync historical data for a profile.

    Called on initial connection to import past data.

    Args:
        db: Database session
        profile_id: Profile ID
        days: Number of days of history to import (default: 30)

    Returns:
        Dictionary with sync results
    """
    today = get_today()
    start_date = today - timedelta(days=days - 1)  # -1 to include today

    return await sync_profile_date_range(db, profile_id, start_date, today)


async def sync_all_connected_profiles(db: Session) -> Dict[int, Dict]:
    """
    Sync recent data for all profiles with Fitbit connections.

    Used by scheduler for hourly sync.

    Args:
        db: Database session

    Returns:
        Dictionary of {profile_id: sync_results}
    """
    results = {}

    # Get all connections
    connections = db.query(FitbitConnection).all()

    for connection in connections:
        try:
            result = await sync_profile_smart(
                db,
                connection.user_id,
                backfill_days=settings.fitbit_backfill_days
            )
            results[connection.user_id] = result
        except Exception as e:
            print(f"Sync failed for profile {connection.user_id}: {e}")
            results[connection.user_id] = {
                "error": str(e),
                "success_days": 0,
                "error_days": 2,
                "total_metrics": 0
            }

            # Update connection status to error
            connection.last_sync_at = get_now()
            connection.last_sync_status = "error"
            db.commit()

    return results
