"""
Fitbit scheduler service.

Handles:
- APScheduler setup for hourly sync
- Background sync job execution
"""
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
import logging

from app.core.config import settings
from app.core.time import get_timezone
from app.core.db import get_db
from app.services.fitbit_sync import sync_all_connected_profiles


# Configure logging
logger = logging.getLogger(__name__)


# Create scheduler instance
scheduler = AsyncIOScheduler(
    jobstores={
        'default': SQLAlchemyJobStore(url=f"sqlite:///{settings.db_path}")
    },
    timezone=get_timezone()
)


async def sync_all_profiles_job():
    """
    Background job to sync all connected profiles.

    Runs hourly to fetch latest Fitbit data.
    """
    logger.info("Starting Fitbit sync job for all profiles...")

    try:
        db = next(get_db())
        results = await sync_all_connected_profiles(db)
        db.close()

        # Log results
        total_profiles = len(results)
        successful = sum(1 for r in results.values() if r.get("error") is None)
        logger.info(
            f"Fitbit sync job complete: {successful}/{total_profiles} profiles synced successfully"
        )

        # Log details for each profile
        for profile_id, result in results.items():
            if result.get("error"):
                logger.error(f"Profile {profile_id} sync failed: {result['error']}")
            else:
                logger.info(
                    f"Profile {profile_id}: {result['success_days']} days synced, "
                    f"{result['total_metrics']} metrics"
                )

    except Exception as e:
        logger.error(f"Fitbit sync job failed: {e}", exc_info=True)


def start_scheduler():
    """
    Start the APScheduler with hourly Fitbit sync job.

    Called during FastAPI app startup.
    """
    # Add hourly sync job
    scheduler.add_job(
        sync_all_profiles_job,
        'interval',
        hours=settings.fitbit_sync_interval_hours,
        id='fitbit_sync',
        replace_existing=True,
        max_instances=1  # Prevent overlapping runs
    )

    scheduler.start()
    logger.info(
        f"Fitbit scheduler started. Sync interval: {settings.fitbit_sync_interval_hours} hour(s)"
    )


def shutdown_scheduler():
    """
    Shutdown the APScheduler.

    Called during FastAPI app shutdown.
    """
    if scheduler.running:
        scheduler.shutdown(wait=True)
        logger.info("Fitbit scheduler shut down")
