"""
Household Maintenance Service Layer

CRITICAL ARCHITECTURE NOTE:
Unlike other services, household tasks are SHARED across all profiles (no profile_id filtering).
profile_id is ONLY used for completion attribution (tracking WHO completed a task).
"""
from typing import List, Optional, Dict
from datetime import date, timedelta
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


def calculate_next_due_date(task: HouseholdTask, from_date: Optional[date] = None) -> Optional[date]:
    """
    Calculate the next due date for a task based on its calendar recurrence pattern.

    This implements calendar-based recurrence (e.g., "every Monday", "1st of month")
    rather than interval-based recurrence (e.g., "7 days after completion").

    Args:
        task: The household task with recurrence configuration
        from_date: Calculate from this date (default: today)

    Returns:
        Next due date, or None for to-do items without due date
    """
    if from_date is None:
        from_date = get_today()

    # To-do items use their explicit due_date (not calculated)
    if task.frequency == 'todo':
        return task.due_date

    # Weekly: Find next occurrence of specified day of week
    if task.frequency == 'weekly':
        if task.recurrence_day_of_week is None:
            # Fallback for tasks without recurrence configured
            return from_date

        # Python weekday: 0=Monday, 6=Sunday (matches our storage format)
        current_weekday = from_date.weekday()
        target_weekday = task.recurrence_day_of_week

        # Days until next occurrence
        days_ahead = (target_weekday - current_weekday) % 7
        if days_ahead == 0:
            # If it's the same day, it's due today
            days_ahead = 0

        return from_date + timedelta(days=days_ahead)

    # Monthly: Find next occurrence of specified day of month
    if task.frequency == 'monthly':
        if task.recurrence_day_of_month is None:
            return from_date

        target_day = task.recurrence_day_of_month

        # Try current month first
        try:
            next_date = from_date.replace(day=target_day)
            if next_date >= from_date:
                return next_date
        except ValueError:
            # Day doesn't exist in current month (e.g., Feb 31)
            pass

        # Try next month
        next_month = from_date.month + 1
        next_year = from_date.year
        if next_month > 12:
            next_month = 1
            next_year += 1

        # Handle months with fewer days
        while True:
            try:
                return date(next_year, next_month, target_day)
            except ValueError:
                # This day doesn't exist in this month, try next month
                next_month += 1
                if next_month > 12:
                    next_month = 1
                    next_year += 1

    # Quarterly: 1st day of 1st month of each quarter (Jan 1, Apr 1, Jul 1, Oct 1)
    if task.frequency == 'quarterly':
        if task.recurrence_month is None or task.recurrence_day is None:
            return from_date

        # Quarters start in months 1, 4, 7, 10
        quarter_start_months = [1, 4, 7, 10]
        target_month_of_quarter = task.recurrence_month  # 1-12, but we interpret 1-3
        target_day = task.recurrence_day

        # Map to actual month (1-3 maps to quarters)
        # Month 1 = first month of quarter (1, 4, 7, 10)
        # Month 2 = second month of quarter (2, 5, 8, 11)
        # Month 3 = third month of quarter (3, 6, 9, 12)

        current_quarter = (from_date.month - 1) // 3  # 0, 1, 2, 3

        for i in range(4):  # Check up to 4 quarters ahead
            quarter = (current_quarter + i) % 4
            base_month = quarter_start_months[quarter]
            actual_month = base_month + (target_month_of_quarter - 1)
            year = from_date.year + ((current_quarter + i) // 4)

            try:
                next_date = date(year, actual_month, target_day)
                if next_date >= from_date:
                    return next_date
            except ValueError:
                continue

        return from_date  # Fallback

    # Annual: Specific date each year (e.g., "March 15th")
    if task.frequency == 'annual':
        if task.recurrence_month is None or task.recurrence_day is None:
            return from_date

        target_month = task.recurrence_month
        target_day = task.recurrence_day

        # Try current year first
        try:
            next_date = date(from_date.year, target_month, target_day)
            if next_date >= from_date:
                return next_date
        except ValueError:
            pass  # Invalid date (e.g., Feb 30)

        # Try next year
        try:
            return date(from_date.year + 1, target_month, target_day)
        except ValueError:
            # Fallback for invalid dates
            return from_date

    return from_date  # Fallback


def is_task_due(task: HouseholdTask, last_completion: Optional[HouseholdCompletion] = None) -> bool:
    """
    Check if a task is currently due based on calendar recurrence.

    A task is due if:
    - It has never been completed, OR
    - The next due date (after last completion) has arrived

    Args:
        task: The household task
        last_completion: Most recent completion record

    Returns:
        True if task is currently due
    """
    today = get_today()

    # To-do items are due if not completed
    if task.frequency == 'todo':
        if last_completion:
            return False  # Already completed
        if task.due_date:
            return today >= task.due_date
        return True  # No due date, always visible until completed

    # Never completed = due now
    if not last_completion:
        return True

    # Calculate next due date after last completion
    completion_date = last_completion.completed_at.date()
    next_due = calculate_next_due_date(task, from_date=completion_date + timedelta(days=1))

    if next_due is None:
        return False

    return today >= next_due


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
                         sort_order: int = 0,
                         recurrence_day_of_week: Optional[int] = None,
                         recurrence_day_of_month: Optional[int] = None,
                         recurrence_month: Optional[int] = None,
                         recurrence_day: Optional[int] = None) -> HouseholdTask:
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
        recurrence_day_of_week: 0-6 (Mon-Sun) for weekly tasks
        recurrence_day_of_month: 1-31 for monthly tasks
        recurrence_month: 1-12 for annual/quarterly tasks
        recurrence_day: 1-31 for annual tasks

    Returns:
        Created HouseholdTask
    """
    # Auto-assign icon if not provided
    if icon is None:
        icon = get_default_icon(title)

    # Set default recurrence values based on frequency if not provided
    if recurrence_day_of_week is None and frequency == 'weekly':
        recurrence_day_of_week = 0  # Default to Monday

    if recurrence_day_of_month is None and frequency == 'monthly':
        recurrence_day_of_month = 1  # Default to 1st of month

    if frequency in ['quarterly', 'annual']:
        if recurrence_month is None:
            recurrence_month = 1  # Default to first month (Jan for annual, 1st month of quarter for quarterly)
        if recurrence_day is None:
            recurrence_day = 1  # Default to 1st day

    task = HouseholdTask(
        title=title,
        description=description,
        frequency=frequency,
        due_date=due_date,
        icon=icon,
        sort_order=sort_order,
        is_active=True,
        recurrence_day_of_week=recurrence_day_of_week,
        recurrence_day_of_month=recurrence_day_of_month,
        recurrence_month=recurrence_month,
        recurrence_day=recurrence_day
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def update_household_task(db: Session, task_id: int, title: Optional[str] = None,
                         description: Optional[str] = None, frequency: Optional[str] = None,
                         due_date: Optional[date] = None, icon: Optional[str] = None,
                         sort_order: Optional[int] = None, is_active: Optional[bool] = None,
                         recurrence_day_of_week: Optional[int] = None,
                         recurrence_day_of_month: Optional[int] = None,
                         recurrence_month: Optional[int] = None,
                         recurrence_day: Optional[int] = None) -> Optional[HouseholdTask]:
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
        recurrence_day_of_week: 0-6 (Mon-Sun) for weekly tasks
        recurrence_day_of_month: 1-31 for monthly tasks
        recurrence_month: 1-12 for annual/quarterly tasks
        recurrence_day: 1-31 for annual tasks

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
    if recurrence_day_of_week is not None:
        task.recurrence_day_of_week = recurrence_day_of_week
    if recurrence_day_of_month is not None:
        task.recurrence_day_of_month = recurrence_day_of_month
    if recurrence_month is not None:
        task.recurrence_month = recurrence_month
    if recurrence_day is not None:
        task.recurrence_day = recurrence_day

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

    # Calculate next due date based on calendar recurrence
    next_due_date = calculate_next_due_date(task)
    is_due = is_task_due(task, last_completion)

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
        # Recurrence configuration
        'recurrence_day_of_week': task.recurrence_day_of_week,
        'recurrence_day_of_month': task.recurrence_day_of_month,
        'recurrence_month': task.recurrence_month,
        'recurrence_day': task.recurrence_day,
        # Completion status
        'last_completed_at': None,
        'last_completed_by_profile_id': None,
        'last_completed_by_profile_name': None,
        'days_since_completion': None,
        # Calendar-based due status
        'next_due_date': next_due_date,
        'is_due': is_due,
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

        # Calculate is_overdue using calendar-based logic
        # Task is overdue if it's due but was completed before the current due date
        today = get_today()
        if task.frequency == 'todo':
            # To-do tasks: never overdue if completed
            is_overdue = False
        elif next_due_date:
            # Recurring tasks: overdue if due date has passed and not completed since then
            completion_date = last_completion.completed_at.date()
            # Task is overdue if today >= next due date AND last completion was before next due date
            is_overdue = today >= next_due_date and completion_date < next_due_date
        else:
            is_overdue = False

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
        today = get_today()
        if task.frequency == 'todo' and task.due_date:
            # To-do items: overdue if past due date
            result['is_overdue'] = today > task.due_date
        elif next_due_date:
            # Recurring tasks: overdue if past due date
            result['is_overdue'] = today > next_due_date

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
