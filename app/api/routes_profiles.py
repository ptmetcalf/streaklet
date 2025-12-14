from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.db import get_db
from app.schemas.profile import ProfileCreate, ProfileUpdate, ProfileResponse
from app.services import profiles as profile_service

router = APIRouter(prefix="/api/profiles", tags=["profiles"])


@router.get("", response_model=List[ProfileResponse])
def list_profiles(db: Session = Depends(get_db)):
    """List all profiles."""
    return profile_service.get_profiles(db)


@router.post("", response_model=ProfileResponse, status_code=201)
def create_profile(profile: ProfileCreate, db: Session = Depends(get_db)):
    """Create a new profile with sample tasks."""
    created_profile = profile_service.create_profile(db, profile)
    if not created_profile:
        raise HTTPException(status_code=409, detail="Profile name already exists")
    return created_profile


@router.get("/{profile_id}", response_model=ProfileResponse)
def get_profile(profile_id: int, db: Session = Depends(get_db)):
    """Get a single profile by ID."""
    profile = profile_service.get_profile_by_id(db, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.put("/{profile_id}", response_model=ProfileResponse)
def update_profile(profile_id: int, profile: ProfileUpdate, db: Session = Depends(get_db)):
    """Update a profile."""
    updated_profile = profile_service.update_profile(db, profile_id, profile)
    if not updated_profile:
        raise HTTPException(status_code=404, detail="Profile not found or name already exists")
    return updated_profile


@router.delete("/{profile_id}", status_code=204)
def delete_profile(profile_id: int, db: Session = Depends(get_db)):
    """Delete a profile (cascade deletes all user data)."""
    success = profile_service.delete_profile(db, profile_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot delete profile (not found or last remaining profile)")
    return None
