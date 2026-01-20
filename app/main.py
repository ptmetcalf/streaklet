from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
import logging

from app.core.db import engine, get_db, Base
from app.api import routes_tasks, routes_days, routes_streaks, routes_history, routes_profiles, routes_fitbit, routes_punch_list, routes_scheduled, routes_household
from app.services import tasks as task_service, profiles as profile_service


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
async def home(request: Request):
    """Home page with today's checklist - data fetched client-side."""
    return templates.TemplateResponse("index.html", {
        "request": request
    })


@app.get("/settings", response_class=HTMLResponse)
async def settings(request: Request):
    """Settings page for managing tasks."""
    return templates.TemplateResponse("settings.html", {
        "request": request
    })


@app.get("/fitbit", response_class=HTMLResponse)
async def fitbit(request: Request):
    """Fitbit metrics viewing page."""
    return templates.TemplateResponse("fitbit.html", {
        "request": request
    })


@app.get("/household", response_class=HTMLResponse)
async def household(request: Request):
    """Household maintenance tracker page."""
    return templates.TemplateResponse("household.html", {
        "request": request
    })


@app.get("/history", response_class=HTMLResponse)
async def history(request: Request):
    """History page showing calendar of completed days - data fetched client-side."""
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

    # Pass default values for template - actual data fetched client-side
    return templates.TemplateResponse("history.html", {
        "request": request,
        "year": year,
        "month": month,
        "calendar_data": {"days_in_month": 0, "first_day_weekday": 0, "days": {}},
        "streak": {"current_streak": 0, "today_complete": False, "last_completed_date": None},
        "today": today.isoformat()
    })


@app.get("/profiles", response_class=HTMLResponse)
async def profiles(request: Request):
    """Profile management page for selecting and managing user profiles."""
    return templates.TemplateResponse("profiles.html", {
        "request": request
    })


@app.get("/health")
async def health():
    """Health check endpoint for Docker."""
    return {"status": "healthy"}
