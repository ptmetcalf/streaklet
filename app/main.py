from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
import os

from app.core.db import engine, get_db, Base
from app.api import routes_tasks, routes_days, routes_streaks
from app.services import tasks as task_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database and seed default tasks on startup."""
    Base.metadata.create_all(bind=engine)

    db = next(get_db())
    try:
        task_service.seed_default_tasks(db)
    finally:
        db.close()

    yield


app = FastAPI(title="Streaklet", lifespan=lifespan)

app.mount("/static", StaticFiles(directory="app/web/static"), name="static")
templates = Jinja2Templates(directory="app/web/templates")

app.include_router(routes_tasks.router)
app.include_router(routes_days.router)
app.include_router(routes_streaks.router)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    """Home page with today's checklist."""
    from app.services import checks as check_service
    from app.services import streaks as streak_service
    from app.core.time import get_today

    today = get_today()
    check_service.ensure_checks_exist_for_date(db, today)

    active_tasks = task_service.get_active_tasks(db)
    checks_map = {
        check.task_id: check
        for check in check_service.get_checks_for_date(db, today)
    }

    tasks_with_checks = []
    for task in active_tasks:
        check = checks_map.get(task.id)
        tasks_with_checks.append({
            "id": task.id,
            "title": task.title,
            "sort_order": task.sort_order,
            "is_required": task.is_required,
            "is_active": task.is_active,
            "checked": check.checked if check else False,
            "checked_at": check.checked_at.isoformat() if check and check.checked_at else None,
        })

    streak_info = streak_service.get_streak_info(db)
    is_complete = check_service.is_day_complete(db, today)

    from app.models.daily_status import DailyStatus
    daily_status = db.query(DailyStatus).filter(DailyStatus.date == today).first()

    day_data = {
        "date": today,
        "tasks": tasks_with_checks,
        "all_required_complete": is_complete,
        "completed_at": daily_status.completed_at if daily_status else None,
        "streak": streak_info,
    }

    return templates.TemplateResponse("index.html", {
        "request": request,
        "day_data": day_data
    })


@app.get("/settings", response_class=HTMLResponse)
async def settings(request: Request):
    """Settings page for managing tasks."""
    return templates.TemplateResponse("settings.html", {
        "request": request
    })


@app.get("/health")
async def health():
    """Health check endpoint for Docker."""
    return {"status": "healthy"}
