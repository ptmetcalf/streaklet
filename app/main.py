from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
import os

from app.core.db import engine, get_db, Base
from app.api import routes_tasks, routes_days, routes_streaks, routes_history, routes_profiles
from app.services import tasks as task_service, history as history_service, profiles as profile_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database, run migrations, and seed default profile on startup."""
    Base.metadata.create_all(bind=engine)

    db = next(get_db())
    try:
        # Seed default profile (will only create if it doesn't exist)
        profile_service.seed_default_profile(db)
        # Seed default tasks for profile 1 (will only create if none exist)
        task_service.seed_default_tasks(db, profile_id=1)
    finally:
        db.close()

    yield


app = FastAPI(title="Streaklet", lifespan=lifespan)

app.mount("/static", StaticFiles(directory="app/web/static"), name="static")
templates = Jinja2Templates(directory="app/web/templates")

app.include_router(routes_tasks.router)
app.include_router(routes_days.router)
app.include_router(routes_streaks.router)
app.include_router(routes_history.router)
app.include_router(routes_profiles.router)


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


@app.get("/history", response_class=HTMLResponse)
async def history(request: Request):
    """History page showing calendar of completed days - data fetched client-side."""
    from app.core.time import get_today

    today = get_today()
    # Pass default values for template - actual data should be fetched client-side
    return templates.TemplateResponse("history.html", {
        "request": request,
        "year": today.year,
        "month": today.month,
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
