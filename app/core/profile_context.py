from fastapi import Cookie
from typing import Optional


def get_profile_id(profile_id: Optional[int] = Cookie(None)) -> int:
    """
    Dependency to extract profile ID from profile_id cookie.
    Defaults to profile 1 if not provided.
    """
    return profile_id if profile_id else 1
