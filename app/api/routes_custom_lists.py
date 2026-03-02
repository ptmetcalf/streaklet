"""API routes for profile-scoped custom lists."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.profile_context import get_profile_id
from app.schemas.custom_list import (
    CustomListCreate,
    CustomListItemCreate,
    CustomListReorderRequest,
    CustomListResponse,
    CustomListUpdate,
)
from app.schemas.task import TaskResponse
from app.services import custom_lists

router = APIRouter(prefix="/api/custom-lists", tags=["custom-lists"])


@router.get("", response_model=list[CustomListResponse])
def list_custom_lists(
    include_disabled: bool = False,
    db: Session = Depends(get_db),
    profile_id: int = Depends(get_profile_id)
):
    return custom_lists.get_custom_lists(db, profile_id, include_disabled=include_disabled)


@router.post("", response_model=CustomListResponse, status_code=201)
def create_custom_list(
    payload: CustomListCreate,
    db: Session = Depends(get_db),
    profile_id: int = Depends(get_profile_id)
):
    try:
        return custom_lists.create_custom_list(db, payload, profile_id)
    except IntegrityError as exc:
        raise HTTPException(status_code=409, detail="Custom list name already exists") from exc


@router.put("/reorder", response_model=list[CustomListResponse])
def reorder_custom_lists(
    payload: CustomListReorderRequest,
    db: Session = Depends(get_db),
    profile_id: int = Depends(get_profile_id)
):
    return custom_lists.reorder_custom_lists(db, profile_id, payload.list_ids)


@router.get("/items", response_model=list[TaskResponse])
def list_all_custom_list_items(
    include_completed: bool = True,
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    profile_id: int = Depends(get_profile_id)
):
    return custom_lists.list_all_custom_list_items(
        db,
        profile_id=profile_id,
        include_completed=include_completed,
        include_inactive=include_inactive,
    )


@router.put("/{list_id}", response_model=CustomListResponse)
def update_custom_list(
    list_id: int,
    payload: CustomListUpdate,
    db: Session = Depends(get_db),
    profile_id: int = Depends(get_profile_id)
):
    try:
        custom_list = custom_lists.update_custom_list(db, list_id, payload, profile_id)
    except IntegrityError as exc:
        raise HTTPException(status_code=409, detail="Custom list name already exists") from exc
    if not custom_list:
        raise HTTPException(status_code=404, detail="Custom list not found")
    return custom_list


@router.delete("/{list_id}", status_code=204)
def delete_custom_list(
    list_id: int,
    db: Session = Depends(get_db),
    profile_id: int = Depends(get_profile_id)
):
    deleted = custom_lists.delete_custom_list(db, list_id, profile_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Custom list not found")
    return None


@router.get("/{list_id}/items", response_model=list[TaskResponse])
def list_custom_list_items(
    list_id: int,
    include_completed: bool = True,
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    profile_id: int = Depends(get_profile_id)
):
    if not custom_lists.get_custom_list_by_id(db, list_id, profile_id):
        raise HTTPException(status_code=404, detail="Custom list not found")
    return custom_lists.list_custom_list_items(
        db,
        list_id=list_id,
        profile_id=profile_id,
        include_completed=include_completed,
        include_inactive=include_inactive,
    )


@router.post("/{list_id}/items", response_model=TaskResponse, status_code=201)
def create_custom_list_item(
    list_id: int,
    payload: CustomListItemCreate,
    db: Session = Depends(get_db),
    profile_id: int = Depends(get_profile_id)
):
    item = custom_lists.create_custom_list_item(db, list_id, payload, profile_id)
    if not item:
        raise HTTPException(status_code=404, detail="Custom list not found")
    return item


@router.post("/{list_id}/items/{item_id}/complete", response_model=TaskResponse)
def complete_custom_list_item(
    list_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    profile_id: int = Depends(get_profile_id)
):
    item = custom_lists.complete_custom_list_item(db, list_id, item_id, profile_id)
    if not item:
        raise HTTPException(status_code=404, detail="Custom list item not found")
    return item


@router.delete("/{list_id}/items/{item_id}/complete", response_model=TaskResponse)
def uncomplete_custom_list_item(
    list_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    profile_id: int = Depends(get_profile_id)
):
    item = custom_lists.uncomplete_custom_list_item(db, list_id, item_id, profile_id)
    if not item:
        raise HTTPException(status_code=404, detail="Custom list item not found")
    return item


@router.delete("/{list_id}/items/{item_id}")
def delete_custom_list_item(
    list_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    profile_id: int = Depends(get_profile_id)
):
    deleted = custom_lists.delete_custom_list_item(db, list_id, item_id, profile_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Custom list item not found")
    return {"message": "Custom list item deleted successfully"}
