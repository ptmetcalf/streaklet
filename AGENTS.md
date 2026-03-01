# AGENTS.md

Project context for AI coding agents (OpenAI Codex, etc.).

## Overview

Streaklet is a self-hosted daily habit streak tracker with multi-user profile support. FastAPI + SQLAlchemy + SQLite backend, Jinja2 + Alpine.js frontend. Designed for family/household use without authentication.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt ruff
```

Always activate the venv before running tests or lint.

## Test Commands

```bash
source .venv/bin/activate

# Run all tests
python -m pytest tests/ -v

# Run a single test file
python -m pytest tests/test_tasks.py -v

# Run a single test function
python -m pytest tests/test_tasks.py::test_create_task -v

# Run with coverage
python -m pytest tests/ --cov=app --cov-report=term
```

## Lint

```bash
source .venv/bin/activate

# CI check (errors and undefined names only)
ruff check app/ tests/ --select=E9,F63,F7,F82

# Full lint
ruff check app/ tests/

# Auto-fix
ruff check app/ tests/ --fix
```

## Commit Format

All commits must use conventional commit format (enforced by release-please):

```
feat: add X
fix: resolve Y
refactor: simplify Z
test: add tests for W
chore: update dependencies
```

`feat:` → minor version bump. `fix:` → patch bump. `feat!:` / `BREAKING CHANGE:` → major bump.

## Architecture

### Profile Isolation (Critical)

Every user profile is fully isolated. All service functions accept `profile_id`:

```python
# Route — always add get_profile_id dependency
@router.get("/api/something")
def get_something(db: Session = Depends(get_db), profile_id: int = Depends(get_profile_id)):
    return service.get_something(db, profile_id)

# Service — always filter by user_id
def get_something(db: Session, profile_id: int):
    return db.query(Model).filter(Model.user_id == profile_id).all()
```

### Timezone

Never use `date.today()` or `datetime.now()`. Always use:
```python
from app.core.time import get_today, get_now
```

### Task Types

Three `task_type` values: `daily`, `punch_list`, `scheduled`.
- `daily`: recurring tasks that count toward streak
- `punch_list`: one-off todos, do not affect streak
- `scheduled`: tasks with a specific due date/recurrence

### Database Schema

Profile-specific tables have `user_id` FK:
- `profiles`, `tasks` (user_id), `task_checks` (user_id), `daily_status` (composite PK: date + user_id)

SQLite does **not** support `ALTER COLUMN SET NOT NULL`. Use table-rebuild pattern for migrations.

### Adding a New Model

1. Add `user_id = Column(Integer, ForeignKey("profiles.id"), nullable=False, index=True)`
2. Pydantic schema in `app/schemas/`
3. Service functions accept `profile_id`, filter by `user_id`
4. Route uses `profile_id: int = Depends(get_profile_id)`
5. Alembic migration
6. Test fixture depends on `sample_profiles`

## Test Fixture Rules

`sample_profiles` must be created before any other fixture that creates profile-scoped data:

```python
@pytest.fixture
def sample_tasks(test_db: Session, sample_profiles):  # depend on sample_profiles
    tasks = [Task(user_id=1, title="Example", task_type="daily", is_active=True)]
    ...
```

All service calls in tests must pass `profile_id=1` (or appropriate value).

## Key Files

| File | Purpose |
|------|---------|
| `app/main.py` | FastAPI app, page routes, lifespan startup |
| `app/core/profile_context.py` | `get_profile_id()` dependency |
| `app/core/time.py` | Timezone-aware `get_today()`, `get_now()` |
| `app/core/encryption.py` | `encrypt_token()`, `decrypt_token()` for Fitbit OAuth tokens |
| `app/services/checks.py` | `recompute_daily_completion()` — recalculates streak on check/uncheck |
| `app/services/streaks.py` | `calculate_current_streak()` |
| `app/services/tasks.py` | Task CRUD + `DEFAULT_TASKS` seed data |
| `tests/conftest.py` | Shared fixtures |
