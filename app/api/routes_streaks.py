from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.profile_context import get_profile_id
from app.schemas.streak import StreakResponse
from app.services import streaks as streak_service

router = APIRouter(prefix="/api/streak", tags=["streaks"])


@router.get("", response_model=StreakResponse)
def get_streak(
    db: Session = Depends(get_db),
    profile_id: int = Depends(get_profile_id)
):
    """Get current streak information for a profile."""
    streak_info = streak_service.get_streak_info(db, profile_id)
    return StreakResponse(**streak_info)
