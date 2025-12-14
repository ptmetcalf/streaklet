from fastapi import Header
from typing import Optional


def get_profile_id(x_profile_id: Optional[int] = Header(None)) -> int:
    """
    Dependency to extract profile ID from X-Profile-Id header.
    Defaults to profile 1 if not provided.
    """
    return x_profile_id if x_profile_id else 1
