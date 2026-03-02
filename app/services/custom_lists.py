"""Service for profile-scoped custom lists and list items."""

from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.time import get_now, get_today
from app.models.custom_list import CustomList
from app.models.profile import Profile
from app.models.task import Task
from app.models.task_check import TaskCheck
from app.schemas.custom_list import CustomListCreate, CustomListUpdate, CustomListItemCreate

DEFAULT_CUSTOM_LIST_TEMPLATES = [
    {
        "template_key": "shopping",
        "name": "Shopping",
        "icon": "cart-outline",
        "sort_order": 1,
        "is_enabled": True,
    },
    {
        "template_key": "grocery",
        "name": "Grocery",
        "icon": "basket-outline",
        "sort_order": 2,
        "is_enabled": False,
    },
    {
        "template_key": "xmas",
        "name": "Xmas List",
        "icon": "gift-outline",
        "sort_order": 3,
        "is_enabled": False,
    },
]


def ensure_default_custom_lists_for_profile(db: Session, profile_id: int) -> None:
    """Ensure template-based lists exist for a profile."""
    profile_exists = db.query(Profile.id).filter(Profile.id == profile_id).first()
    if not profile_exists:
        return

    existing_by_template = {
        row.template_key: row
        for row in db.query(CustomList).filter(
            CustomList.user_id == profile_id,
            CustomList.template_key.isnot(None)
        ).all()
    }

    changed = False
    for template in DEFAULT_CUSTOM_LIST_TEMPLATES:
        template_key = template["template_key"]
        if template_key in existing_by_template:
            continue
        db.add(CustomList(
            user_id=profile_id,
            name=template["name"],
            icon=template["icon"],
            template_key=template_key,
            is_enabled=template["is_enabled"],
            sort_order=template["sort_order"],
        ))
        changed = True

    if changed:
        db.commit()


def get_custom_lists(db: Session, profile_id: int, include_disabled: bool = False) -> list[CustomList]:
    """List custom lists for a profile ordered by sort order then name."""
    ensure_default_custom_lists_for_profile(db, profile_id)

    query = db.query(CustomList).filter(CustomList.user_id == profile_id)
    if not include_disabled:
        query = query.filter(CustomList.is_enabled.is_(True))

    return query.order_by(CustomList.sort_order, CustomList.name).all()


def get_custom_list_by_id(db: Session, list_id: int, profile_id: int) -> Optional[CustomList]:
    return db.query(CustomList).filter(
        CustomList.id == list_id,
        CustomList.user_id == profile_id
    ).first()


def get_custom_list_by_template(db: Session, profile_id: int, template_key: str) -> Optional[CustomList]:
    return db.query(CustomList).filter(
        CustomList.user_id == profile_id,
        CustomList.template_key == template_key
    ).first()


def get_or_create_shopping_list(db: Session, profile_id: int) -> CustomList:
    """Compatibility helper for legacy shopping-list endpoints."""
    ensure_default_custom_lists_for_profile(db, profile_id)
    shopping = get_custom_list_by_template(db, profile_id, "shopping")
    if shopping:
        return shopping

    max_sort = db.query(CustomList.sort_order).filter(
        CustomList.user_id == profile_id
    ).order_by(CustomList.sort_order.desc()).first()
    next_sort = (max_sort[0] + 1) if max_sort else 1

    shopping = CustomList(
        user_id=profile_id,
        name="Shopping",
        icon="cart-outline",
        template_key="shopping",
        is_enabled=True,
        sort_order=next_sort,
    )
    db.add(shopping)
    db.commit()
    db.refresh(shopping)
    return shopping


def create_custom_list(db: Session, data: CustomListCreate, profile_id: int) -> CustomList:
    payload = data.model_dump()
    if "sort_order" not in payload or payload["sort_order"] is None:
        max_sort = db.query(CustomList.sort_order).filter(
            CustomList.user_id == profile_id
        ).order_by(CustomList.sort_order.desc()).first()
        payload["sort_order"] = (max_sort[0] + 1) if max_sort else 1

    custom_list = CustomList(user_id=profile_id, **payload)
    db.add(custom_list)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise
    db.refresh(custom_list)
    return custom_list


def update_custom_list(db: Session, list_id: int, data: CustomListUpdate, profile_id: int) -> Optional[CustomList]:
    custom_list = get_custom_list_by_id(db, list_id, profile_id)
    if not custom_list:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(custom_list, key, value)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise
    db.refresh(custom_list)
    return custom_list


def reorder_custom_lists(db: Session, profile_id: int, ordered_ids: list[int]) -> list[CustomList]:
    if not ordered_ids:
        return get_custom_lists(db, profile_id, include_disabled=True)

    lists = db.query(CustomList).filter(
        CustomList.user_id == profile_id,
        CustomList.id.in_(ordered_ids)
    ).all()
    by_id = {item.id: item for item in lists}

    for index, list_id in enumerate(ordered_ids, start=1):
        custom_list = by_id.get(list_id)
        if custom_list:
            custom_list.sort_order = index

    db.commit()
    return get_custom_lists(db, profile_id, include_disabled=True)


def delete_custom_list(db: Session, list_id: int, profile_id: int) -> bool:
    custom_list = get_custom_list_by_id(db, list_id, profile_id)
    if not custom_list:
        return False

    # Explicit delete of list tasks keeps behavior deterministic on SQLite even
    # if the database was not migrated with an FK constraint.
    db.query(Task).filter(
        Task.user_id == profile_id,
        Task.custom_list_id == list_id
    ).delete()
    db.delete(custom_list)
    db.commit()
    return True


def list_custom_list_items(
    db: Session,
    list_id: int,
    profile_id: int,
    include_completed: bool = True,
    include_inactive: bool = False
) -> list[Task]:
    query = db.query(Task).filter(
        Task.user_id == profile_id,
        Task.task_type == "custom_list",
        Task.custom_list_id == list_id
    )

    if not include_inactive:
        query = query.filter(Task.is_active.is_(True))
    if not include_completed:
        query = query.filter(Task.completed_at.is_(None))

    return query.order_by(Task.completed_at.isnot(None), Task.created_at.desc()).all()


def list_all_custom_list_items(
    db: Session,
    profile_id: int,
    include_completed: bool = True,
    include_inactive: bool = False
) -> list[Task]:
    query = db.query(Task).filter(
        Task.user_id == profile_id,
        Task.task_type == "custom_list"
    )
    if not include_inactive:
        query = query.filter(Task.is_active.is_(True))
    if not include_completed:
        query = query.filter(Task.completed_at.is_(None))
    return query.order_by(Task.completed_at.isnot(None), Task.created_at.desc()).all()


def create_custom_list_item(
    db: Session,
    list_id: int,
    item: CustomListItemCreate,
    profile_id: int
) -> Optional[Task]:
    custom_list = get_custom_list_by_id(db, list_id, profile_id)
    if not custom_list:
        return None

    from app.services.tasks import get_default_task_icon

    item_data = item.model_dump()
    if not item_data.get("icon"):
        item_data["icon"] = get_default_task_icon(item_data["title"])

    db_item = Task(
        user_id=profile_id,
        custom_list_id=list_id,
        title=item_data["title"],
        icon=item_data["icon"],
        task_type="custom_list",
        is_required=False,
        is_active=True,
        due_date=None,
        active_since=get_today(),
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def _get_custom_list_item(db: Session, list_id: int, item_id: int, profile_id: int) -> Optional[Task]:
    return db.query(Task).filter(
        Task.id == item_id,
        Task.user_id == profile_id,
        Task.task_type == "custom_list",
        Task.custom_list_id == list_id
    ).first()


def complete_custom_list_item(db: Session, list_id: int, item_id: int, profile_id: int) -> Optional[Task]:
    item = _get_custom_list_item(db, list_id, item_id, profile_id)
    if not item:
        return None

    now = get_now()
    today = get_today()
    item.completed_at = now

    check = db.query(TaskCheck).filter(
        TaskCheck.date == today,
        TaskCheck.task_id == item_id,
        TaskCheck.user_id == profile_id
    ).first()
    if not check:
        check = TaskCheck(
            date=today,
            task_id=item_id,
            user_id=profile_id,
            checked=True,
            checked_at=now
        )
        db.add(check)
    else:
        check.checked = True
        check.checked_at = now

    db.commit()
    db.refresh(item)
    return item


def uncomplete_custom_list_item(db: Session, list_id: int, item_id: int, profile_id: int) -> Optional[Task]:
    item = _get_custom_list_item(db, list_id, item_id, profile_id)
    if not item:
        return None

    item.completed_at = None

    today = get_today()
    check = db.query(TaskCheck).filter(
        TaskCheck.date == today,
        TaskCheck.task_id == item_id,
        TaskCheck.user_id == profile_id
    ).first()
    if check:
        check.checked = False
        check.checked_at = None

    db.commit()
    db.refresh(item)
    return item


def delete_custom_list_item(db: Session, list_id: int, item_id: int, profile_id: int) -> bool:
    item = _get_custom_list_item(db, list_id, item_id, profile_id)
    if not item:
        return False

    db.delete(item)
    db.commit()
    return True
