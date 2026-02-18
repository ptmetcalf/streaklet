from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
import logging
import time

from app.core.db import engine, get_db, Base
from app.core.profile_context import get_profile_id
from app.api import routes_tasks, routes_days, routes_streaks, routes_history, routes_profiles, routes_fitbit, routes_punch_list, routes_scheduled, routes_household
from app.services import tasks as task_service, profiles as profile_service

# Cache bust value for static assets (prevents browser caching issues)
CACHE_BUST = str(int(time.time()))


# Configure application logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:     %(name)s - %(message)s'
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database, run migrations, seed default profile, and start scheduler on startup."""
    Base.metadata.create_all(bind=engine)

    db = next(get_db())
    try:
        # Seed default profile (will only create if it doesn't exist)
        profile_service.seed_default_profile(db)
        # Seed default tasks for profile 1 (will only create if none exist)
        task_service.seed_default_tasks(db, profile_id=1)
    finally:
        db.close()

    # Start Fitbit sync scheduler
    from app.services.fitbit_scheduler import start_scheduler, shutdown_scheduler
    start_scheduler()

    yield

    # Shutdown scheduler
    shutdown_scheduler()


app = FastAPI(title="Streaklet", lifespan=lifespan)

app.mount("/static", StaticFiles(directory="app/web/static"), name="static")
templates = Jinja2Templates(directory="app/web/templates")

app.include_router(routes_tasks.router)
app.include_router(routes_days.router)
app.include_router(routes_streaks.router)
app.include_router(routes_history.router)
app.include_router(routes_profiles.router)
app.include_router(routes_fitbit.router)
app.include_router(routes_punch_list.router)
app.include_router(routes_scheduled.router)
app.include_router(routes_household.router)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db), profile_id: int = Depends(get_profile_id)):
    """Home page with today's checklist."""
    from app.services import checks as check_service
    from app.services import streaks as streak_service
    from app.core.time import get_today
    from app.models.task import Task
    from sqlalchemy import and_, or_

    today = get_today()

    # Ensure checks exist for today
    check_service.ensure_checks_exist_for_date(db, today, profile_id)

    # Get daily tasks and scheduled tasks that are due today
    daily_tasks_query = db.query(Task).filter(
        and_(
            Task.is_active.is_(True),
            Task.user_id == profile_id,
            or_(
                Task.task_type == 'daily',
                and_(
                    Task.task_type == 'scheduled',
                    Task.next_occurrence_date == today
                )
            )
        )
    ).order_by(Task.sort_order).all()

    # Get checks for today
    checks_map = {
        check.task_id: check
        for check in check_service.get_checks_for_date(db, today, profile_id)
    }

    # Import services for Fitbit progress and task streaks
    from app.services.fitbit_checks import get_task_fitbit_progress

    # Build tasks with check status
    daily_tasks = []
    for task in daily_tasks_query:
        check = checks_map.get(task.id)

        # Get Fitbit progress if task has Fitbit goal
        fitbit_progress = {}
        if task.fitbit_metric_type and task.fitbit_goal_value:
            fitbit_progress = get_task_fitbit_progress(db, task, today, profile_id)

        # Calculate per-task streak
        task_streak, last_completed = streak_service.calculate_task_streak(db, task.id, profile_id)

        # Determine next milestone
        milestones = [3, 7, 14, 21, 30, 45, 60, 90, 100, 180, 365]
        next_milestone = next((m for m in milestones if m > task_streak), None)

        task_dict = {
            "id": task.id,
            "title": task.title,
            "icon": task.icon,
            "sort_order": task.sort_order,
            "is_required": task.is_required,
            "is_active": task.is_active,
            "checked": check.checked if check else False,
            "task_type": task.task_type,
            # Fitbit fields
            "fitbit_metric_type": task.fitbit_metric_type,
            "fitbit_goal_value": task.fitbit_goal_value,
            "fitbit_goal_operator": task.fitbit_goal_operator,
            "fitbit_auto_check": task.fitbit_auto_check,
            # Fitbit progress
            "fitbit_current_value": fitbit_progress.get("current_value"),
            "fitbit_goal_met": fitbit_progress.get("goal_met", False),
            "fitbit_unit": fitbit_progress.get("unit"),
            # Per-task streak
            "task_streak": task_streak,
            "task_last_completed": last_completed.isoformat() if last_completed else None,
            "task_streak_milestone": next_milestone,
        }
        daily_tasks.append(task_dict)

    # Get punch list tasks
    punch_list_tasks_query = db.query(Task).filter(
        and_(
            Task.task_type == 'punch_list',
            Task.user_id == profile_id
        )
    ).order_by(Task.sort_order).all()

    punch_list_tasks = []
    for task in punch_list_tasks_query:
        task_dict = {
            "id": task.id,
            "title": task.title,
            "icon": task.icon,
            "sort_order": task.sort_order,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "due_date": task.due_date.isoformat() if task.due_date else None
        }
        punch_list_tasks.append(task_dict)

    # Get streak info
    streak_info = streak_service.get_streak_info(db, profile_id)

    # Convert date objects to strings for JSON serialization
    streak_json = {
        "current_streak": streak_info["current_streak"],
        "today_complete": streak_info["today_complete"],
        "last_completed_date": streak_info["last_completed_date"].isoformat() if streak_info["last_completed_date"] else None,
        "today_date": streak_info["today_date"].isoformat() if streak_info["today_date"] else None
    }

    return templates.TemplateResponse("index.html", {
        "request": request,
        "daily_tasks": daily_tasks,
        "punch_list_tasks": punch_list_tasks,
        "streak": streak_json,
        "date": today.isoformat(),
        "cache_bust": CACHE_BUST
    })


@app.get("/settings", response_class=HTMLResponse)
async def settings(request: Request):
    """Settings page for managing tasks."""
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "cache_bust": CACHE_BUST
    })


@app.get("/fitbit", response_class=HTMLResponse)
async def fitbit(request: Request, db: Session = Depends(get_db), profile_id: int = Depends(get_profile_id)):
    """Fitbit metrics viewing page."""
    from app.services import fitbit_connection
    from app.core.time import get_today

    # Check Fitbit connection status server-side
    connection = fitbit_connection.get_connection(db, profile_id)
    fitbit_connected = connection is not None
    today = get_today()

    return templates.TemplateResponse("fitbit.html", {
        "request": request,
        "fitbit_connected": fitbit_connected,
        "today": today.isoformat(),
        "cache_bust": CACHE_BUST
    })


@app.get("/household", response_class=HTMLResponse)
async def household(request: Request, db: Session = Depends(get_db)):
    """Household maintenance tracker page."""
    from app.services import household as household_service

    # Fetch initial tasks server-side (household tasks are shared, no profile_id)
    tasks = household_service.get_all_tasks_with_status(db)

    # Convert datetime/date objects to strings for JSON serialization
    tasks_json = []
    for task in tasks:
        task_copy = task.copy()
        # Convert datetime fields
        if task_copy.get('due_date'):
            task_copy['due_date'] = task_copy['due_date'].isoformat()
        if task_copy.get('created_at'):
            task_copy['created_at'] = task_copy['created_at'].isoformat()
        if task_copy.get('updated_at'):
            task_copy['updated_at'] = task_copy['updated_at'].isoformat()
        if task_copy.get('last_completed_at'):
            task_copy['last_completed_at'] = task_copy['last_completed_at'].isoformat()
        if task_copy.get('next_due_date'):
            task_copy['next_due_date'] = task_copy['next_due_date'].isoformat()
        tasks_json.append(task_copy)

    return templates.TemplateResponse("household.html", {
        "request": request,
        "tasks": tasks_json,
        "cache_bust": CACHE_BUST
    })


@app.get("/history", response_class=HTMLResponse)
async def history(request: Request, db: Session = Depends(get_db), profile_id: int = Depends(get_profile_id)):
    """History page showing calendar of completed days."""
    from app.services import history as history_service
    from app.services import streaks as streak_service
    from app.core.time import get_today

    today = get_today()
    year_param = request.query_params.get("year")
    month_param = request.query_params.get("month")

    try:
        year = int(year_param) if year_param is not None else today.year
    except ValueError:
        year = today.year

    try:
        month = int(month_param) if month_param is not None else today.month
    except ValueError:
        month = today.month

    if not (1 <= month <= 12):
        month = today.month

    if not (2000 <= year <= 2100):
        year = today.year

    # Fetch real data server-side
    calendar_data = history_service.get_calendar_month_data(db, year, month, profile_id)
    streak_info = streak_service.get_streak_info(db, profile_id)

    # Convert date objects to strings for JSON serialization
    streak_json = {
        "current_streak": streak_info["current_streak"],
        "today_complete": streak_info["today_complete"],
        "last_completed_date": streak_info["last_completed_date"].isoformat() if streak_info["last_completed_date"] else None
    }

    return templates.TemplateResponse("history.html", {
        "request": request,
        "year": year,
        "month": month,
        "calendar_data": calendar_data,
        "streak": streak_json,
        "today": today.isoformat(),
        "cache_bust": CACHE_BUST
    })


@app.get("/profiles", response_class=HTMLResponse)
async def profiles(request: Request):
    """Profile management page for selecting and managing user profiles."""
    return templates.TemplateResponse("profiles.html", {
        "request": request,
        "cache_bust": CACHE_BUST
    })


@app.get("/health")
async def health():
    """Health check endpoint for Docker."""
    return {"status": "healthy"}
