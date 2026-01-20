"""
Fitbit connection management service.

Handles:
- Retrieving connection status
- Deleting connections
- Resetting Fitbit task settings
"""
from sqlalchemy.orm import Session
from typing import Optional

from app.models.fitbit_connection import FitbitConnection
from app.models.task import Task
from app.services.fitbit_oauth import revoke_token


def get_connection(db: Session, profile_id: int) -> Optional[FitbitConnection]:
    """
    Get Fitbit connection for a profile.

    Args:
        db: Database session
        profile_id: Profile ID

    Returns:
        FitbitConnection if exists, None otherwise
    """
    return db.query(FitbitConnection).filter(
        FitbitConnection.user_id == profile_id
    ).first()


async def delete_connection(db: Session, profile_id: int) -> bool:
    """
    Delete Fitbit connection and all associated data.

    This performs the following actions:
    1. Revokes access token with Fitbit (best-effort)
    2. Deletes FitbitConnection record (CASCADE deletes metrics)
    3. Resets fitbit_auto_check on all tasks to False

    Args:
        db: Database session
        profile_id: Profile ID

    Returns:
        True if connection was deleted, False if no connection existed
    """
    connection = get_connection(db, profile_id)
    if not connection:
        return False

    # Revoke token with Fitbit (best-effort, errors are logged)
    await revoke_token(connection)

    # Delete connection (CASCADE will delete metrics)
    db.delete(connection)

    # Reset auto-check on all tasks (keep other Fitbit fields for re-connection)
    db.query(Task).filter(
        Task.user_id == profile_id,
        Task.fitbit_auto_check .is_(True)
    ).update({"fitbit_auto_check": False})

    db.commit()

    return True


def get_connection_status(db: Session, profile_id: int) -> dict:
    """
    Get connection status for a profile.

    Args:
        db: Database session
        profile_id: Profile ID

    Returns:
        Dictionary with connection status information
    """
    connection = get_connection(db, profile_id)

    if not connection:
        return {
            "connected": False,
            "fitbit_user_id": None,
            "connected_at": None,
            "last_sync_at": None,
            "last_sync_status": None
        }

    return {
        "connected": True,
        "fitbit_user_id": connection.fitbit_user_id,
        "connected_at": connection.connected_at,
        "last_sync_at": connection.last_sync_at,
        "last_sync_status": connection.last_sync_status
    }
