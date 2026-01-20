"""
Household Maintenance Service Layer

CRITICAL ARCHITECTURE NOTE:
Unlike other services, household tasks are SHARED across all profiles (no profile_id filtering).
profile_id is ONLY used for completion attribution (tracking WHO completed a task).
"""
from typing import List, Optional, Dict
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.household_task import HouseholdTask
from app.models.household_completion import HouseholdCompletion
from app.models.profile import Profile
from app.core.time import get_now, get_today


# Frequency thresholds in days
FREQUENCY_THRESHOLDS = {
    'weekly': 7,
    'monthly': 30,
    'quarterly': 90,
    'annual': 365
}

# Default icon mappings based on task keywords
DEFAULT_ICONS = {
    # Cleaning
    'clean': 'spray-bottle',
    'vacuum': 'robot-vacuum',
    'mop': 'water',
    'dust': 'weather-dust',
    'sweep': 'broom',
    'scrub': 'dishwasher',
    'wipe': 'paper-roll',

    # Bathroom
    'toilet': 'toilet',
    'bathroom': 'shower',
    'shower': 'shower',
    'bath': 'bathtub',

    # Kitchen
    'kitchen': 'silverware-fork-knife',
    'dish': 'dishwasher',
    'oven': 'stove',
    'microwave': 'microwave',
    'refrigerator': 'fridge',
    'fridge': 'fridge',

    # Laundry
    'laundry': 'washing-machine',
    'wash': 'tshirt-crew',
    'dry': 'tumble-dryer',
    'iron': 'iron',

    # Outdoor/Garden
    'lawn': 'grass',
    'mow': 'lawnmower',
    'garden': 'flower',
    'plant': 'sprout',
    'leaf': 'leaf',
    'leaves': 'leaf',
    'yard': 'tree',
    'gutter': 'home-roof',

    # Maintenance
    'fix': 'wrench',
    'repair': 'tools',
    'replace': 'swap-horizontal',
    'filter': 'air-filter',
    'hvac': 'air-conditioner',
    'air': 'air-conditioner',
    'check': 'clipboard-check',
    'inspect': 'magnify',
    'test': 'test-tube',

    # Trash/Recycling
    'trash': 'delete',
    'garbage': 'delete',
    'recycle': 'recycle',
    'compost': 'sprout',

    # Pets
    'pet': 'paw',
    'dog': 'dog',
    'cat': 'cat',
    'feed': 'bowl-mix',

    # Vehicles
    'car': 'car',
    'vehicle': 'car-wash',
    'oil': 'oil',

    # Windows/Doors
    'window': 'window-closed',
    'door': 'door',
    'lock': 'lock',

    # General
    'water': 'water',
    'paint': 'format-paint',
    'organize': 'folder-multiple',
}


def get_default_icon(title: str) -> str:
    """
    Get a sensible default icon based on task title keywords.

    Args:
        title: Task title to analyze

    Returns:
        Material Design Icon name (default: 'checkbox-marked-circle')
    """
    title_lower = title.lower()

    # Check for keyword matches
    for keyword, icon in DEFAULT_ICONS.items():
        if keyword in title_lower:
            return icon

    # Default fallback icon
    return 'checkbox-marked-circle'


def get_all_household_tasks(db: Session, include_inactive: bool = False) -> List[HouseholdTask]:
    """
    Get all household tasks (SHARED - no profile filtering).

    Args:
        db: Database session
        include_inactive: Whether to include inactive tasks

    Returns:
        List of all household tasks
    """
    query = db.query(HouseholdTask)
    if not include_inactive:
        query = query.filter(HouseholdTask.is_active .is_(True))
    return query.order_by(HouseholdTask.sort_order, HouseholdTask.id).all()


def get_household_tasks_by_frequency(db: Session, frequency: str, include_inactive: bool = False) -> List[HouseholdTask]:
    """
    Get household tasks filtered by frequency.

    Args:
        db: Database session
        frequency: One of 'weekly', 'monthly', 'quarterly', 'annual'
        include_inactive: Whether to include inactive tasks

    Returns:
        List of household tasks with matching frequency
    """
    query = db.query(HouseholdTask).filter(HouseholdTask.frequency == frequency)
    if not include_inactive:
        query = query.filter(HouseholdTask.is_active .is_(True))
    return query.order_by(HouseholdTask.sort_order, HouseholdTask.id).all()


def get_household_task_by_id(db: Session, task_id: int) -> Optional[HouseholdTask]:
    """Get a single household task by ID."""
    return db.query(HouseholdTask).filter(HouseholdTask.id == task_id).first()


def create_household_task(db: Session, title: str, description: Optional[str], frequency: str,
                         due_date: Optional[date] = None, icon: Optional[str] = None,
                         sort_order: int = 0) -> HouseholdTask:
    """
    Create a new household task (SHARED - no profile association).

    Args:
        db: Database session
        title: Task title
        description: Optional task description
        frequency: One of 'weekly', 'monthly', 'quarterly', 'annual', 'todo'
        due_date: Optional due date (primarily for to-do items)
        icon: Optional Material Design Icon name (auto-assigned if None)
        sort_order: Sort order for display

    Returns:
        Created HouseholdTask
    """
    # Auto-assign icon if not provided
    if icon is None:
        icon = get_default_icon(title)

    task = HouseholdTask(
        title=title,
        description=description,
        frequency=frequency,
        due_date=due_date,
        icon=icon,
        sort_order=sort_order,
        is_active=True
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def update_household_task(db: Session, task_id: int, title: Optional[str] = None,
                         description: Optional[str] = None, frequency: Optional[str] = None,
                         due_date: Optional[date] = None, icon: Optional[str] = None,
                         sort_order: Optional[int] = None, is_active: Optional[bool] = None) -> Optional[HouseholdTask]:
    """
    Update an existing household task.

    Args:
        db: Database session
        task_id: Task ID to update
        title: New title (if provided)
        description: New description (if provided)
        frequency: New frequency (if provided)
        due_date: New due date (if provided)
        icon: New icon (if provided)
        sort_order: New sort order (if provided)
        is_active: New active status (if provided)

    Returns:
        Updated HouseholdTask or None if not found
    """
    task = get_household_task_by_id(db, task_id)
    if not task:
        return None

    if title is not None:
        task.title = title
    if description is not None:
        task.description = description
    if frequency is not None:
        task.frequency = frequency
    if due_date is not None:
        task.due_date = due_date
    if icon is not None:
        task.icon = icon
    if sort_order is not None:
        task.sort_order = sort_order
    if is_active is not None:
        task.is_active = is_active

    task.updated_at = get_now()
    db.commit()
    db.refresh(task)
    return task


def delete_household_task(db: Session, task_id: int) -> bool:
    """
    Delete a household task (cascade deletes completions).

    Args:
        db: Database session
        task_id: Task ID to delete

    Returns:
        True if deleted, False if not found
    """
    task = get_household_task_by_id(db, task_id)
    if not task:
        return False

    db.delete(task)
    db.commit()
    return True


def mark_task_complete(db: Session, task_id: int, profile_id: int, notes: Optional[str] = None) -> Optional[HouseholdCompletion]:
    """
    Mark a household task as completed by a specific profile.

    Args:
        db: Database session
        task_id: Household task ID
        profile_id: Profile ID of who completed the task (ATTRIBUTION ONLY)
        notes: Optional completion notes

    Returns:
        Created HouseholdCompletion or None if task not found
    """
    task = get_household_task_by_id(db, task_id)
    if not task:
        return None

    completion = HouseholdCompletion(
        household_task_id=task_id,
        completed_by_profile_id=profile_id,
        completed_at=get_now(),
        notes=notes
    )
    db.add(completion)
    db.commit()
    db.refresh(completion)
    return completion


def get_last_completion(db: Session, task_id: int) -> Optional[HouseholdCompletion]:
    """
    Get the most recent completion for a task.

    Args:
        db: Database session
        task_id: Household task ID

    Returns:
        Most recent HouseholdCompletion or None
    """
    return (
        db.query(HouseholdCompletion)
        .filter(HouseholdCompletion.household_task_id == task_id)
        .order_by(desc(HouseholdCompletion.completed_at))
        .first()
    )


def get_completion_history(db: Session, task_id: int, limit: int = 10) -> List[Dict]:
    """
    Get completion history for a task with profile names.

    Args:
        db: Database session
        task_id: Household task ID
        limit: Maximum number of completions to return

    Returns:
        List of completion dicts with profile names
    """
    completions = (
        db.query(HouseholdCompletion, Profile.name)
        .join(Profile, HouseholdCompletion.completed_by_profile_id == Profile.id)
        .filter(HouseholdCompletion.household_task_id == task_id)
        .order_by(desc(HouseholdCompletion.completed_at))
        .limit(limit)
        .all()
    )

    return [
        {
            'id': completion.id,
            'household_task_id': completion.household_task_id,
            'completed_at': completion.completed_at,
            'completed_by_profile_id': completion.completed_by_profile_id,
            'completed_by_profile_name': profile_name,
            'notes': completion.notes
        }
        for completion, profile_name in completions
    ]


def get_task_with_status(db: Session, task_id: int) -> Optional[Dict]:
    """
    Get a household task enriched with completion status.

    Adds:
    - due_date: Optional due date (for to-do items)
    - last_completed_at: DateTime of last completion
    - last_completed_by_profile_id: Profile ID of who last completed
    - last_completed_by_profile_name: Name of who last completed
    - days_since_completion: Days since last completion
    - is_overdue: Whether task is overdue based on frequency/due date
    - is_completed: Whether to-do task has been completed (for filtering)

    Returns:
        Dict with task and status info, or None if not found
    """
    task = get_household_task_by_id(db, task_id)
    if not task:
        return None

    last_completion = get_last_completion(db, task_id)

    result = {
        'id': task.id,
        'title': task.title,
        'description': task.description,
        'frequency': task.frequency,
        'due_date': task.due_date,
        'icon': task.icon,
        'sort_order': task.sort_order,
        'is_active': task.is_active,
        'created_at': task.created_at,
        'updated_at': task.updated_at,
        'last_completed_at': None,
        'last_completed_by_profile_id': None,
        'last_completed_by_profile_name': None,
        'days_since_completion': None,
        'is_overdue': False,
        'is_completed': False  # For to-do items
    }

    if last_completion:
        # Get profile name
        profile = db.query(Profile).filter(Profile.id == last_completion.completed_by_profile_id).first()
        profile_name = profile.name if profile else "Unknown"

        # Handle timezone-aware vs naive datetime comparison
        now = get_now()
        completed_at = last_completion.completed_at

        # If completed_at is naive, make it timezone-aware
        if completed_at.tzinfo is None:
            from datetime import timezone
            completed_at = completed_at.replace(tzinfo=timezone.utc)

        # If now is naive, make it timezone-aware
        if now.tzinfo is None:
            from datetime import timezone
            now = now.replace(tzinfo=timezone.utc)

        days_since = (now - completed_at).days

        # For to-do items, mark as completed (will be filtered from list)
        is_todo_completed = task.frequency == 'todo'

        # Calculate is_overdue based on task type
        if task.frequency == 'todo':
            # To-do tasks: overdue only if they have a due_date in the past and aren't completed
            is_overdue = False
            if task.due_date and not is_todo_completed:
                is_overdue = get_today() > task.due_date
        else:
            # Recurring tasks: overdue if days since completion > threshold
            is_overdue = days_since > FREQUENCY_THRESHOLDS.get(task.frequency, 999999)

        result.update({
            'last_completed_at': last_completion.completed_at,
            'last_completed_by_profile_id': last_completion.completed_by_profile_id,
            'last_completed_by_profile_name': profile_name,
            'days_since_completion': days_since,
            'is_overdue': is_overdue,
            'is_completed': is_todo_completed
        })
    else:
        # No completion yet
        # For to-do items with due dates, check if overdue
        if task.frequency == 'todo' and task.due_date:
            result['is_overdue'] = get_today() > task.due_date

    return result


def get_all_tasks_with_status(db: Session, include_inactive: bool = False, include_completed_todos: bool = False) -> List[Dict]:
    """
    Get all household tasks enriched with completion status.

    Args:
        db: Database session
        include_inactive: Whether to include inactive tasks
        include_completed_todos: Whether to include completed to-do items (default: hide them)

    Returns:
        List of dicts with task and status info
    """
    tasks = get_all_household_tasks(db, include_inactive=include_inactive)
    tasks_with_status = [get_task_with_status(db, task.id) for task in tasks]

    # Filter out completed to-dos unless explicitly requested
    if not include_completed_todos:
        tasks_with_status = [t for t in tasks_with_status if not t.get('is_completed', False)]

    return tasks_with_status


def get_overdue_tasks(db: Session) -> List[Dict]:
    """
    Get all overdue household tasks.

    A task is overdue if:
    - It has been completed before AND
    - Days since last completion > frequency threshold

    Never-completed tasks are NOT considered overdue.

    Returns:
        List of overdue tasks with status info
    """
    all_tasks = get_all_tasks_with_status(db, include_inactive=False)
    return [task for task in all_tasks if task['is_overdue']]
