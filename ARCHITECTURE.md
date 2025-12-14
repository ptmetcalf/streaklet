You are my coding agent. Build “Streaklet”, a self-hosted, Dockerized daily streak tracker.

GOAL
A mobile-friendly web app where the landing screen is today’s checklist. Users check off daily tasks. If (and only if) all required tasks are checked for a given day, that day is “completed”. The current streak is the number of consecutive completed days ending at the most recent completed day. If a day is missed/incomplete, the streak resets and the next completed day starts at Day 1. Tasks must be editable.

TECH STACK (required)
- Python 3.12+
- FastAPI
- Pydantic v2 models for request/response schemas
- SQLAlchemy 2.0 ORM
- SQLite database file stored on a mounted Docker volume for persistence
- Alembic migrations
- Tests with pytest, pytest-asyncio, httpx (ASGI client), freezegun (or equivalent time-freezing)
- Dockerfile + docker-compose.yml for homelab use
- Serve a simple mobile-first UI (choose ONE):
  A) Minimal SPA (React + Vite) built to static assets and served by FastAPI
  OR
  B) Server-rendered HTML templates (Jinja2) with a little HTMX/Alpine for interactivity
  Preference: choose B (templates) if you want fastest implementation and simplest deploy.

NON-FUNCTIONAL REQUIREMENTS
- App opens to checklist view (no login required). Assume it’s protected by LAN / reverse proxy.
- Config via env vars:
  - APP_TIMEZONE (default: America/Chicago)
  - DB_PATH (default: /data/app.db)
  - PORT (default: 8080)
- Timezone correctness: “today” is based on APP_TIMEZONE, not UTC.
- Idempotent startup: migrations run automatically on container start.
- Persistent data: DB must live at /data/app.db and be mapped in compose.

FEATURES
1) Default tasks (seed on first run if tasks table empty):
   - Follow a diet
   - 30 minute workout
   - 30 minute workout (yes, keep as separate entry)
   - Read 10 pages
   - 20 minutes of hobby time

2) Task management (Settings screen)
   - Add task (title)
   - Edit task title
   - Toggle is_required (default true)
   - Toggle is_active (default true)
   - Reorder tasks (sort_order)
   - Delete task (soft delete ok)

3) Daily checklist (Home screen)
   - Show today’s date
   - Show “Streak: Day N”
   - Show progress “x/y required done”
   - Checklist with big tap targets
   - Checking/unchecking updates immediately

4) Streak logic
   Definitions:
   - A “required task for a day” = task where is_active=true AND is_required=true at time of evaluation.
   - A day is “completed” when all required tasks for that date are checked.
   - Store completion state in DB so it’s queryable.
   - Streak calculation:
     - Find the most recent date with completed_at not null.
     - Count how many consecutive prior dates also have completed_at not null.
     - That count is current_streak.
   - If today is incomplete, current_streak still reflects last completed run; UI should indicate “Today: In progress”.
   - If user unchecks a required task after completion, that day becomes incomplete and completed_at clears.

DATA MODEL (SQLAlchemy)
Use these tables (names can match):
- tasks:
  id (int pk or uuid), title (text), sort_order (int),
  is_required (bool), is_active (bool),
  created_at (datetime), updated_at (datetime)
- daily_status:
  date (YYYY-MM-DD string or Date, pk),
  completed_at (datetime nullable)
- task_checks:
  date (Date), task_id (fk), checked (bool), checked_at (datetime nullable)
  composite pk (date, task_id)

IMPORTANT BEHAVIOR
- When tasks change, today’s checklist should reflect new tasks:
  - New active tasks appear unchecked by default.
  - Deactivated tasks should not appear in today’s list.
- For days in the past (optional), streak logic must remain consistent with stored daily_status rows.

API (FastAPI)
Implement JSON API for frontend:
- GET  /api/tasks -> list tasks ordered by sort_order
- POST /api/tasks -> create
- PUT  /api/tasks/{id} -> update fields
- DELETE /api/tasks/{id} -> soft/hard delete
- GET  /api/days/today -> returns:
    { date, tasks:[{task fields + checked}], all_required_complete, completed_at, streak:{current_streak, today_complete, last_completed_date} }
- PUT  /api/days/{date}/checks/{task_id} body { checked: bool } -> toggle check, recompute completion
- GET  /api/streak -> { current_streak, today_complete, last_completed_date, today_date }

IMPLEMENTATION STRUCTURE
Use this repo layout:
app/
  main.py
  core/
    config.py        # env vars
    db.py            # engine/session + dependency
    time.py          # timezone-aware “today” helpers
  models/            # SQLAlchemy ORM models
  schemas/           # Pydantic models
  services/
    tasks.py         # CRUD
    checks.py        # toggle logic + daily completion updates
    streaks.py       # streak computation
  api/
    routes_tasks.py
    routes_days.py
    routes_streaks.py
  web/               # templates/static if using server-rendered
migrations/          # alembic
tests/
  conftest.py
  test_tasks.py
  test_daily_checks.py
  test_streaks.py
Dockerfile
docker-compose.yml
README.md

TESTING REQUIREMENTS
- Use dependency override to inject test DB session.
- Provide tests for:
  1) seeding defaults on empty DB
  2) completing all required tasks sets completed_at
  3) unchecking clears completed_at
  4) streak increments for consecutive days
  5) streak resets when a day is missed
  6) task deactivation affects required set and can flip completion
- Use freezegun (or time provider injection) to control “today” and test timezone boundaries.

DOCKER
- Dockerfile builds app, runs alembic upgrade head on start, then runs uvicorn on PORT.
- docker-compose.yml:
  - service “streaklet”
  - ports: 8080:8080
  - volume: ./data:/data
  - env: APP_TIMEZONE, DB_PATH=/data/app.db, PORT=8080

DELIVERABLES
- Working app with UI + API
- One-command run: docker compose up --build
- Clear README with:
  - how to run
  - env vars
  - how persistence works
  - how to run tests locally

Make sensible choices, keep it minimal, and focus on correctness of streak logic and mobile usability.
