from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.task import Task
from app.models.task_check import TaskCheck
from app.schemas.task import TaskCreate, TaskUpdate
from typing import List, Optional, Dict, Any
from datetime import timedelta, datetime, time


# Default icon mappings for personal tasks
DEFAULT_TASK_ICONS = {
    # Fitness & Health
    'walk': 'walk',
    'step': 'shoe-print',
    'run': 'run',
    'exercise': 'dumbbell',
    'workout': 'weight-lifter',
    'gym': 'weight-lifter',
    'yoga': 'yoga',
    'stretch': 'human-handsup',
    'bike': 'bike',
    'swim': 'swim',

    # Health
    'sleep': 'sleep',
    'rest': 'bed',
    'meditate': 'meditation',
    'medicine': 'pill',
    'vitamin': 'pill',
    'water': 'water',
    'hydrate': 'cup-water',

    # Food & Diet
    'eat': 'food-apple',
    'meal': 'silverware-fork-knife',
    'breakfast': 'coffee',
    'lunch': 'food',
    'dinner': 'food-turkey',
    'cook': 'chef-hat',
    'protein': 'food-steak',
    'vegetable': 'carrot',
    'fruit': 'food-apple',

    # Mental & Productivity
    'read': 'book-open-variant',
    'book': 'book',
    'study': 'school',
    'learn': 'head-lightbulb',
    'write': 'pencil',
    'journal': 'notebook',
    'plan': 'calendar-check',

    # Hobbies & Creative
    'hobby': 'palette',
    'creative': 'brush',
    'art': 'palette',
    'music': 'music',
    'play': 'gamepad-variant',
    'practice': 'music-note',
    'guitar': 'guitar-acoustic',
    'piano': 'piano',

    # Social & Relationships
    'call': 'phone',
    'text': 'message',
    'family': 'account-group',
    'friend': 'account-multiple',
    'social': 'account-group',

    # Work & Productivity
    'work': 'briefcase',
    'email': 'email',
    'meeting': 'calendar-account',
    'project': 'folder-multiple',

    # Self-care
    'shower': 'shower',
    'skincare': 'face-woman',
    'teeth': 'tooth',
    'brush': 'toothbrush',
    'floss': 'tooth',

    # Chores
    'clean': 'broom',
    'laundry': 'washing-machine',
    'dishes': 'dishwasher',
    'trash': 'delete',

    # Misc
    'active': 'run-fast',
    'minute': 'clock-outline',
    'time': 'clock',
    'daily': 'calendar-today',
    'goal': 'flag-checkered',
}


def get_default_task_icon(title: str) -> str:
    """
    Get a sensible default icon based on task title keywords.

    Args:
        title: Task title to analyze

    Returns:
        Material Design Icon name (default: 'check-circle')
    """
    title_lower = title.lower()

    # Check for keyword matches
    for keyword, icon in DEFAULT_TASK_ICONS.items():
        if keyword in title_lower:
            return icon

    # Default fallback icon
    return 'check-circle'


DEFAULT_TASKS = [
    {
        "title": "Walk 10,000 steps",
        "sort_order": 1,
        "is_required": True,
        "is_active": True,
        "task_type": "daily",
        "fitbit_metric_type": "steps",
        "fitbit_goal_value": 10000,
        "fitbit_goal_operator": "gte",
        "fitbit_auto_check": False  # User enables when connecting Fitbit
    },
    {
        "title": "Sleep 7+ hours",
        "sort_order": 2,
        "is_required": True,
        "is_active": True,
        "task_type": "daily",
        "fitbit_metric_type": "sleep_minutes",
        "fitbit_goal_value": 420,
        "fitbit_goal_operator": "gte",
        "fitbit_auto_check": False
    },
    {
        "title": "30 minutes active",
        "sort_order": 3,
        "is_required": True,
        "is_active": True,
        "task_type": "daily",
        "fitbit_metric_type": "active_minutes",
        "fitbit_goal_value": 30,
        "fitbit_goal_operator": "gte",
        "fitbit_auto_check": False
    },
    {
        "title": "Read 10 pages",
        "sort_order": 4,
        "is_required": True,
        "is_active": True,
        "task_type": "daily"
    },
    {
        "title": "20 minutes of hobby time",
        "sort_order": 5,
        "is_required": True,
        "is_active": True,
        "task_type": "daily"
    },
]


def seed_default_tasks(db: Session, profile_id: int = 1) -> None:
    """Seed default tasks for a specific profile if no tasks exist for that profile."""
    count = db.query(func.count(Task.id)).filter(Task.user_id == profile_id).scalar()
    if count == 0:
        for task_data in DEFAULT_TASKS:
            task = Task(**task_data, user_id=profile_id)
            db.add(task)
        db.commit()


def get_tasks(db: Session, profile_id: int) -> List[Task]:
    """Get all tasks for a profile ordered by sort_order."""
    return db.query(Task).filter(Task.user_id == profile_id).order_by(Task.sort_order).all()


def get_active_tasks(db: Session, profile_id: int) -> List[Task]:
    """Get all active tasks for a profile ordered by sort_order."""
    return db.query(Task).filter(
        Task.user_id == profile_id,
        Task.is_active .is_(True)
    ).order_by(Task.sort_order).all()


def get_task_by_id(db: Session, task_id: int, profile_id: int) -> Optional[Task]:
    """Get a task by ID for a specific profile."""
    return db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == profile_id
    ).first()


def create_task(db: Session, task: TaskCreate, profile_id: int) -> Task:
    """Create a new task for a profile."""
    from app.core.time import get_today

    task_data = task.model_dump()

    # Set active_since to today if not provided
    if task_data.get('active_since') is None:
        task_data['active_since'] = get_today()

    # Auto-assign icon if not provided
    if task_data.get('icon') is None:
        task_data['icon'] = get_default_task_icon(task_data['title'])

    db_task = Task(**task_data, user_id=profile_id)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


def update_task(db: Session, task_id: int, task_update: TaskUpdate, profile_id: int) -> Optional[Task]:
    """Update a task for a profile."""
    db_task = get_task_by_id(db, task_id, profile_id)
    if not db_task:
        return None

    update_data = task_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_task, key, value)

    db.commit()
    db.refresh(db_task)
    return db_task


def delete_task(db: Session, task_id: int, profile_id: int) -> bool:
    """Delete a task for a profile (hard delete)."""
    db_task = get_task_by_id(db, task_id, profile_id)
    if not db_task:
        return False

    db.delete(db_task)
    db.commit()
    return True


def _calculate_best_streak(dates: List) -> int:
    """Calculate longest consecutive daily streak from a list of dates."""
    if not dates:
        return 0

    sorted_dates = sorted(set(dates))
    best = 1
    current = 1

    for index in range(1, len(sorted_dates)):
        if sorted_dates[index] == sorted_dates[index - 1] + timedelta(days=1):
            current += 1
        else:
            current = 1
        best = max(best, current)

    return best


def get_task_history(db: Session, task_id: int, profile_id: int, limit: int = 30) -> Optional[Dict[str, Any]]:
    """
    Get completion history and summary stats for a personal task.

    Supports both recurring tasks (via task_checks) and one-off list tasks
    (single completion timestamp on the task record).
    """
    from app.core.time import get_today
    from app.services import streaks as streak_service

    task = get_task_by_id(db, task_id, profile_id)
    if not task:
        return None

    today = get_today()
    cutoff_date = today - timedelta(days=29)

    if task.task_type in ('punch_list', 'shopping_list'):
        history = []
        total_completions = 0
        completions_last_30_days = 0
        last_completed_at = task.completed_at

        if task.completed_at:
            source = 'punch_list' if task.task_type == 'punch_list' else 'shopping_list'
            history = [{
                'date': task.completed_at.date(),
                'completed_at': task.completed_at,
                'source': source
            }]
            total_completions = 1
            if task.completed_at.date() >= cutoff_date:
                completions_last_30_days = 1

        return {
            'task_id': task.id,
            'task_type': task.task_type,
            'stats': {
                'total_completions': total_completions,
                'completions_last_30_days': completions_last_30_days,
                'current_streak': 0,
                'best_streak': 0,
                'last_completed_at': last_completed_at
            },
            'history': history
        }

    recent_checks = db.query(TaskCheck).filter(
        TaskCheck.task_id == task.id,
        TaskCheck.user_id == profile_id,
        TaskCheck.checked.is_(True)
    ).order_by(TaskCheck.date.desc()).limit(limit).all()

    all_check_dates = [
        row[0] for row in db.query(TaskCheck.date).filter(
            TaskCheck.task_id == task.id,
            TaskCheck.user_id == profile_id,
            TaskCheck.checked.is_(True)
        ).all()
    ]

    total_completions = len(all_check_dates)
    completions_last_30_days = db.query(TaskCheck).filter(
        TaskCheck.task_id == task.id,
        TaskCheck.user_id == profile_id,
        TaskCheck.checked.is_(True),
        TaskCheck.date >= cutoff_date
    ).count()

    current_streak, _ = streak_service.calculate_task_streak(db, task.id, profile_id)
    best_streak = _calculate_best_streak(all_check_dates)
    last_completed_at = recent_checks[0].checked_at if recent_checks else None
    if recent_checks and last_completed_at is None:
        last_completed_at = datetime.combine(recent_checks[0].date, time.min)

    history = []
    for check in recent_checks:
        completed_at = check.checked_at or datetime.combine(check.date, time.min)
        history.append({
            'date': check.date,
            'completed_at': completed_at,
            'source': 'check'
        })

    return {
        'task_id': task.id,
        'task_type': task.task_type,
        'stats': {
            'total_completions': total_completions,
            'completions_last_30_days': completions_last_30_days,
            'current_streak': current_streak,
            'best_streak': best_streak,
            'last_completed_at': last_completed_at
        },
        'history': history
    }
