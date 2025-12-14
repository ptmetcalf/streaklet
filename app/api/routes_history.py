from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.services import history as history_service
from typing import Dict, Any

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("/{year}/{month}")
def get_month_history(
    year: int,
    month: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get calendar history data for a specific month."""
    if not (1 <= month <= 12):
        raise HTTPException(status_code=400, detail="Month must be between 1 and 12")

    if not (2000 <= year <= 2100):
        raise HTTPException(status_code=400, detail="Year must be between 2000 and 2100")

    calendar_data = history_service.get_calendar_month_data(db, year, month)
    stats = history_service.get_month_completion_stats(db, year, month)

    return {
        'year': year,
        'month': month,
        'calendar_data': calendar_data,
        'stats': stats
    }
