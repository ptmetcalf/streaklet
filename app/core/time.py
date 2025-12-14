from datetime import datetime, date
from zoneinfo import ZoneInfo
from app.core.config import settings


def get_timezone() -> ZoneInfo:
    """Get the configured timezone."""
    return ZoneInfo(settings.app_timezone)


def get_now() -> datetime:
    """Get current datetime in the configured timezone."""
    return datetime.now(get_timezone())


def get_today() -> date:
    """Get today's date in the configured timezone."""
    return get_now().date()


def to_timezone_aware(dt: datetime) -> datetime:
    """Convert a datetime to timezone-aware using the configured timezone."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=get_timezone())
    return dt.astimezone(get_timezone())
