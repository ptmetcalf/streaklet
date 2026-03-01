from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
import logging
import time

from app.core.db import engine, get_db, Base
from app.core.profile_context import get_profile_id
from app.api import (
    routes_tasks,
    routes_days,
    routes_streaks,
    routes_history,
    routes_profiles,
    routes_fitbit,
    routes_punch_list,
    routes_scheduled,
    routes_household,
    routes_shopping_list,
)
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
app.include_router(routes_shopping_list.router)


@app.get("/sw.js")
async def service_worker():
    """Serve service worker from root for proper PWA scope and legacy browser checks."""
    return FileResponse("app/web/static/sw.js", media_type="application/javascript")


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

    # Get punch list tasks (exclude archived)
    punch_list_tasks_query = db.query(Task).filter(
        and_(
            Task.task_type == 'punch_list',
            Task.user_id == profile_id,
            Task.archived_at.is_(None)
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

    # Get shopping list items
    shopping_list_tasks_query = db.query(Task).filter(
        and_(
            Task.task_type == 'shopping_list',
            Task.user_id == profile_id,
            Task.is_active.is_(True)
        )
    ).order_by(Task.completed_at.isnot(None), Task.created_at.desc()).all()

    shopping_list_tasks = []
    for task in shopping_list_tasks_query:
        task_dict = {
            "id": task.id,
            "title": task.title,
            "icon": task.icon,
            "sort_order": task.sort_order,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        }
        shopping_list_tasks.append(task_dict)

    # Get streak info
    streak_info = streak_service.get_streak_info(db, profile_id)

    # Convert date objects to strings for JSON serialization
    streak_json = {
        "current_streak": streak_info["current_streak"],
        "today_complete": streak_info["today_complete"],
        "last_completed_date": streak_info["last_completed_date"].isoformat() if streak_info["last_completed_date"] else None,
        "today_date": streak_info["today_date"].isoformat() if streak_info["today_date"] else None
    }

    return templates.TemplateResponse(request, "index.html", {
        "request": request,
        "daily_tasks": daily_tasks,
        "punch_list_tasks": punch_list_tasks,
        "shopping_list_tasks": shopping_list_tasks,
        "streak": streak_json,
        "date": today.isoformat(),
        "cache_bust": CACHE_BUST
    })


@app.get("/settings", response_class=HTMLResponse)
async def settings(request: Request):
    """Settings page for preferences, profiles, and integrations."""
    return templates.TemplateResponse(request, "settings.html", {
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

    return templates.TemplateResponse(request, "fitbit.html", {
        "request": request,
        "fitbit_connected": fitbit_connected,
        "today": today.isoformat(),
        "cache_bust": CACHE_BUST
    })


@app.get("/household", response_class=HTMLResponse)
async def household(request: Request, db: Session = Depends(get_db)):
    """Household maintenance tracker page."""
    from app.services import household as household_service

    # Fetch initial tasks server-side including inactive so archived tasks render immediately
    tasks = household_service.get_all_tasks_with_status(db, include_inactive=True)

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

    return templates.TemplateResponse(request, "household.html", {
        "request": request,
        "tasks": tasks_json,
        "cache_bust": CACHE_BUST
    })


@app.get("/history", response_class=RedirectResponse)
async def history(request: Request):
    """Redirect old /history bookmarks to the home page (history is now a tab on the today page)."""
    return RedirectResponse(url="/", status_code=301)


@app.get("/profiles", response_class=HTMLResponse)
async def profiles(request: Request):
    """Profile management page for selecting and managing user profiles."""
    return templates.TemplateResponse(request, "profiles.html", {
        "request": request,
        "cache_bust": CACHE_BUST
    })


@app.get("/health")
async def health():
    """Health check endpoint for Docker."""
    return {"status": "healthy"}
