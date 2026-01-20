from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response, Form
from sqlalchemy.orm import Session
from typing import List
import json
from app.core.db import get_db
from app.schemas.profile import ProfileCreate, ProfileUpdate, ProfileResponse
from app.services import profiles as profile_service
from app.services import backup as backup_service

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


@router.get("/{profile_id}/export")
def export_profile(profile_id: int, db: Session = Depends(get_db)):
    """
    Export all data for a profile in JSON format.

    Returns a downloadable JSON file containing:
    - Profile information
    - All tasks
    - All task checks
    - All daily completion records
    """
    export_data = backup_service.export_profile_data(db, profile_id)
    if not export_data:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Get profile name for filename
    profile = profile_service.get_profile_by_id(db, profile_id)
    filename = f"streaklet_{profile.name.replace(' ', '_').lower()}_backup.json"

    # Return as downloadable JSON file
    return Response(
        content=json.dumps(export_data, indent=2),
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@router.post("/{profile_id}/import", status_code=200)
async def import_profile(
    profile_id: int,
    file: UploadFile = File(...),
    mode: str = Form("replace"),
    db: Session = Depends(get_db)
):
    """
    Import profile data from a JSON backup file.

    Args:
        profile_id: Target profile ID to import into
        file: JSON backup file
        mode: Import mode - 'replace' (delete existing data) or 'merge' (keep existing)

    Returns success message or error.
    """
    # Validate mode
    if mode not in ["replace", "merge"]:
        raise HTTPException(status_code=400, detail="Invalid mode. Must be 'replace' or 'merge'")

    # Check profile exists (unless it will be created in replace mode)
    profile = profile_service.get_profile_by_id(db, profile_id)
    if not profile and mode == "merge":
        raise HTTPException(status_code=404, detail="Profile not found")

    # Read and parse JSON file
    try:
        content = await file.read()
        data = json.loads(content)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")

    # Import data
    success, error = backup_service.import_profile_data(db, data, profile_id=profile_id, mode=mode)
    if not success:
        raise HTTPException(status_code=400, detail=error)

    return {
        "message": f"Profile data imported successfully in {mode} mode",
        "profile_id": profile_id
    }


@router.get("/export/all")
def export_all_profiles(db: Session = Depends(get_db)):
    """
    Export data for all profiles in JSON format.

    Returns a downloadable JSON file containing all profiles and their data.
    """
    export_data = backup_service.export_all_profiles(db)

    filename = "streaklet_all_profiles_backup.json"

    return Response(
        content=json.dumps(export_data, indent=2),
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@router.post("/import/all", status_code=200)
async def import_all_profiles(
    file: UploadFile = File(...),
    mode: str = Form("replace"),
    db: Session = Depends(get_db)
):
    """
    Import data for all profiles from a JSON backup file.

    Args:
        file: JSON backup file (all profiles format)
        mode: Import mode - 'replace' (delete existing data) or 'merge' (keep existing)

    Returns success message or error.
    """
    # Validate mode
    if mode not in ["replace", "merge"]:
        raise HTTPException(status_code=400, detail="Invalid mode. Must be 'replace' or 'merge'")

    # Read and parse JSON file
    try:
        content = await file.read()
        data = json.loads(content)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")

    # Import data
    success, error = backup_service.import_all_profiles(db, data, mode=mode)
    if not success:
        raise HTTPException(status_code=400, detail=error)

    return {
        "message": f"All profiles imported successfully in {mode} mode",
        "profile_count": len(data.get("profiles", []))
    }
