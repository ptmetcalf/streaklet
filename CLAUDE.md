# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Streaklet is a self-hosted daily habit streak tracker with multi-user profile support. Built with FastAPI, SQLAlchemy, and SQLite, designed for family/household use without authentication. Each profile has completely isolated data (tasks, checks, streaks, history).

## CI/CD Pipeline

The repository has automated CI/CD workflows:

### GitHub Actions Workflows

**`ci.yml`** - Comprehensive CI pipeline (runs on all pushes/PRs):
- **Lint**: Code quality checks with ruff
- **Test**: Unit tests with coverage reporting
- **Test Docker**: Builds Docker image and runs tests inside container
- **Integration**: Spins up full stack and tests API endpoints
- **Test Summary**: Aggregates all test results

**`docker-publish.yml`** - Docker image publishing (runs on main branch/tags):
- Runs tests first
- Builds multi-platform Docker image (amd64, arm64)
- Publishes to GitHub Container Registry (ghcr.io)

All workflows must pass before merging PRs.

### Coverage Reports

Coverage reports are generated in CI and uploaded to Codecov (if configured). Local coverage:
```bash
pytest --cov=app --cov-report=html
# Open htmlcov/index.html in browser
```

Configuration in `.coveragerc` excludes tests, migrations, and templates from coverage.

## Development Commands

### Setup Local Environment

**Important**: Use a virtual environment for local development to avoid system package conflicts.

```bash
# Create virtual environment (first time only)
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt ruff

# When done working
deactivate
```

The `.venv` directory is git-ignored. Always activate the venv before running tests or linting locally.

### Docker Development
```bash
# Build and run with Docker Compose
docker compose up --build

# Run tests inside Docker
docker build -t streaklet . && docker run --rm --entrypoint "" streaklet sh -c "PYTHONPATH=. python -m pytest tests/ -v"

# Rebuild and restart container after code changes
docker stop streaklet && docker rm streaklet && docker run -d --name streaklet -p 8080:8080 -v streaklet-data:/data streaklet
```

### Local Development
```bash
# Activate venv first (if not already)
source .venv/bin/activate

# Run development server
./dev.sh run
# OR: uvicorn app.main:app --reload --host 0.0.0.0 --port 8080

# Run all tests
./dev.sh test
# OR: python -m pytest tests/ -v

# Run single test file
python -m pytest tests/test_profiles.py -v

# Run single test function
python -m pytest tests/test_profiles.py::test_create_profile -v

# Run tests with coverage
./dev.sh test-cov
# OR: python -m pytest tests/ --cov=app --cov-report=html --cov-report=term
```

### Database Migrations
```bash
# Run migrations
./dev.sh migrate
# OR: alembic upgrade head

# Create new migration
./dev.sh migrate-new "description"
# OR: alembic revision --autogenerate -m "description"

# Rollback one migration
alembic downgrade -1
```

### Linting and Code Quality
```bash
# Activate venv first (if not already)
source .venv/bin/activate

# Check for syntax errors and undefined names (CI uses this)
ruff check app/ tests/ --select=E9,F63,F7,F82

# Check all rules
ruff check app/ tests/

# Auto-fix issues
ruff check app/ tests/ --fix
```

## Architecture

### Multi-User Profile System (Critical Concept)

**Profile Context Propagation**: The entire application is built around profile isolation using dependency injection.

1. **Frontend**: Browser localStorage stores selected profile ID
2. **HTTP Layer**: `X-Profile-Id` header sent with every API request via `fetchWithProfile()` helper
3. **Dependency Injection**: `get_profile_id()` dependency extracts header (defaults to 1)
4. **Service Layer**: All functions accept `profile_id` parameter and filter data accordingly
5. **Database**: Foreign key constraints enforce data isolation (tasks, task_checks, daily_status all have `user_id`)

**Key Files**:
- `app/core/profile_context.py` - Dependency that extracts profile ID from header
- `app/web/templates/base.html` - Alpine.js store + `fetchWithProfile()` helper
- All service functions in `app/services/` - Must accept and use `profile_id` parameter

**Pattern for New Features**:
```python
# Route
@router.get("/api/something")
def get_something(
    db: Session = Depends(get_db),
    profile_id: int = Depends(get_profile_id)  # Add this dependency
):
    return service.get_something(db, profile_id)

# Service
def get_something(db: Session, profile_id: int):  # Accept profile_id
    return db.query(Model).filter(
        Model.user_id == profile_id  # Filter by profile
    ).all()
```

### Timezone Handling

All date/time operations MUST use timezone-aware functions from `app/core/time.py`:
- `get_today()` - Returns today's date in configured timezone
- `get_now()` - Returns current datetime in configured timezone
- Never use `date.today()` or `datetime.now()` directly

Configurable via `APP_TIMEZONE` environment variable (default: `America/Chicago`).

### Daily Completion Logic

**Key Concept**: A day is complete when ALL required active tasks are checked.

Flow:
1. User checks/unchecks task → API call to `PUT /api/days/{date}/checks/{task_id}`
2. `check_service.update_task_check()` updates the check
3. `recompute_daily_completion()` automatically called:
   - Queries all required active tasks for profile
   - Checks if all are completed
   - Updates or creates `DailyStatus` record with `completed_at` timestamp
4. Streak calculation uses `DailyStatus.completed_at IS NOT NULL` to count consecutive days

**Critical Files**:
- `app/services/checks.py` - Contains `recompute_daily_completion()` logic
- `app/models/daily_status.py` - Composite PK: (date, user_id)

### Streak Calculation

Streaks count consecutive days working BACKWARDS from today/yesterday:
- If today is complete, streak includes today
- If today is incomplete, streak ends at most recent completed day
- Breaks on any day with no completion

See `app/services/streaks.py::calculate_current_streak()` for implementation.

### Template Architecture

All pages use **client-side data fetching** (not SSR):
- Templates render minimal HTML skeleton
- Alpine.js `x-init="await loadData()"` fetches data from API
- `fetchWithProfile()` helper automatically includes `X-Profile-Id` header

**Do not add SSR data** to route functions - keep them minimal and let templates fetch via API.

### Database Schema

**Profile Isolation Pattern**:
- `profiles` table: User profiles (id, name, color)
- `tasks` table: Has `user_id` FK to profiles
- `task_checks` table: Has `user_id` FK to profiles
- `daily_status` table: Composite PK (date, user_id)

**Important**: When adding new tables that should be profile-specific, always add `user_id` FK.

### Test Fixtures

**Critical Dependency Order**: `sample_profiles` must be created before other fixtures.

```python
# Correct
@pytest.fixture
def sample_tasks(test_db: Session, sample_profiles):  # Depends on sample_profiles
    tasks = [Task(user_id=1, ...)]  # Must include user_id

# When creating test data
DailyStatus(date=today, user_id=1, ...)  # Always include user_id
check_service.update_task_check(db, date, task_id, checked, profile_id=1)  # Always pass profile_id
```

All service function calls in tests must include `profile_id` parameter.

## Seeding and Defaults

- **First Run**: Default profile (ID=1, name="Default Profile") auto-created on startup
- **New Profiles**: Automatically seeded with 5 default tasks (see `app/services/tasks.py::DEFAULT_TASKS`)
- Tasks: Follow a diet, 30 min workout, Read 10 pages, 20 min hobby time, Drink 8 glasses water

## SQLite Limitations

**Important for Migrations**: SQLite does NOT support `ALTER COLUMN SET NOT NULL`.

When adding NOT NULL constraints:
1. Add column as nullable
2. Populate data
3. Create new table with constraints
4. Copy data
5. Drop old table, rename new table

See `migrations/versions/002_add_profiles.py` for example.

## API Testing Pattern

Profile-aware endpoints require header:
```bash
# Without header (defaults to profile 1)
curl http://localhost:8080/api/tasks

# With specific profile
curl -H "X-Profile-Id: 2" http://localhost:8080/api/tasks

# Creating/updating with profile
curl -X POST -H "X-Profile-Id: 2" -H "Content-Type: application/json" \
  -d '{"title": "New Task", ...}' \
  http://localhost:8080/api/tasks
```

## Common Patterns

### Adding a New Model with Profile Isolation

1. Model: Add `user_id = Column(Integer, ForeignKey("profiles.id"), nullable=False, index=True)`
2. Schema: Create Pydantic models in `app/schemas/`
3. Service: Functions accept `profile_id`, filter queries by `Model.user_id == profile_id`
4. Routes: Add `profile_id: int = Depends(get_profile_id)` dependency
5. Migration: Create alembic migration with proper FK constraints
6. Tests: Update `conftest.py` with fixture, ensure `sample_profiles` dependency

### Adding a New API Endpoint

```python
# app/api/routes_something.py
from app.core.profile_context import get_profile_id

@router.get("/api/something")
def get_something(
    db: Session = Depends(get_db),
    profile_id: int = Depends(get_profile_id)
):
    return something_service.get_something(db, profile_id)
```

Then include router in `app/main.py`: `app.include_router(routes_something.router)`

### Adding a New Frontend Page

1. Create template in `app/web/templates/something.html` extending `base.html`
2. Add route in `app/main.py`:
   ```python
   @app.get("/something", response_class=HTMLResponse)
   async def something(request: Request):
       return templates.TemplateResponse("something.html", {"request": request})
   ```
3. Use Alpine.js with `x-init="await loadData()"` to fetch data via API
4. Use `fetchWithProfile()` for all API calls to include profile header

## Project Standards

- **FastAPI** with async route handlers where appropriate
- **SQLAlchemy 2.0** with declarative_base (not legacy declarative approach)
- **Pydantic v2** with `ConfigDict` (not class-based `Config`)
- **Alpine.js** for frontend interactivity (NOT React/Vue)
- **HTMX** available but not heavily used
- **Mobile-first** CSS design

## Environment Variables

Set in `docker-compose.yml` or `.env`:
- `APP_TIMEZONE` - Timezone for daily tracking (default: America/Chicago)
- `DB_PATH` - Database file location (default: /data/app.db)
- `PORT` - Application port (default: 8080)
