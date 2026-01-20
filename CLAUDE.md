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

**`docker-publish.yml`** - Docker image publishing (runs on develop branch):
- Runs tests first
- Builds multi-platform Docker image (amd64, arm64)
- Publishes to GitHub Container Registry (ghcr.io)

**`release-please.yml`** - Automated release management (runs on main branch):
- Analyzes commits using conventional commit format
- Creates Release PRs with auto-generated changelogs
- Bumps version numbers automatically (semver)
- Creates GitHub Releases when Release PR is merged
- Builds and publishes Docker images with version tags

All workflows must pass before merging PRs.

### Automated Releases with release-please

This project uses [release-please](https://github.com/googleapis/release-please) for automated releases. **IMPORTANT**: All commits to main must follow the conventional commit format.

#### Conventional Commit Format

Commits must use this format:
```
<type>(<scope>): <description>

[optional body]
[optional footer]
```

**Commit Types** (determines version bump):
- `feat:` - New feature → Minor version bump (1.0.0 → 1.1.0)
- `fix:` - Bug fix → Patch version bump (1.0.0 → 1.0.1)
- `feat!:` or `BREAKING CHANGE:` - Breaking change → Major version bump (1.0.0 → 2.0.0)
- `docs:` - Documentation only (no release)
- `chore:` - Maintenance tasks (no release)
- `refactor:` - Code restructuring (no release)
- `perf:` - Performance improvement → Patch bump
- `test:` - Adding tests (no release)
- `ci:` - CI/CD changes (no release)

**Examples:**
```bash
feat: add dark mode toggle to settings
fix: resolve timezone display issue in Fitbit page
feat!: redesign API authentication

BREAKING CHANGE: API now requires JWT tokens
docs: update installation instructions
chore: update dependencies
```

#### Release Workflow

1. Merge PR to main with conventional commit(s)
2. release-please automatically creates a "Release PR" (titled: `chore(main): release X.Y.Z`)
3. Release PR includes:
   - Auto-calculated version bump
   - Generated CHANGELOG.md
   - Updated version files
4. Review and merge Release PR
5. GitHub Release created automatically
6. Docker images built and published with version tags

**Important for AI assistants**: When making commits, always use conventional commit format. When creating PRs, use conventional commit format in the PR title if using squash merge.

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

## Form Component Patterns

Streaklet uses a standardized BEM-based form component system (introduced in Phase 6) for consistent styling and behavior across all forms.

### Basic Form Field

```html
<div class="form-field">
    <label class="form-field__label">Title</label>
    <input type="text" class="form-field__input"
           x-model="newTask.title"
           placeholder="Task title">
</div>
```

### Required Field

Add the `form-field__label--required` modifier to show an asterisk:

```html
<div class="form-field">
    <label class="form-field__label form-field__label--required">Title</label>
    <input type="text" class="form-field__input"
           x-model="newTask.title"
           required>
</div>
```

### Select Dropdown

```html
<div class="form-field">
    <label class="form-field__label">Frequency</label>
    <select class="form-field__select" x-model="task.frequency">
        <option value="daily">Daily</option>
        <option value="weekly">Weekly</option>
    </select>
</div>
```

### Checkbox

```html
<div class="form-field">
    <label class="form-field__checkbox-label">
        <input type="checkbox" class="form-field__checkbox"
               x-model="task.is_required">
        <span>Required for daily completion</span>
    </label>
</div>
```

### Radio Group

```html
<div class="form-field">
    <label class="form-field__label">Task Type</label>
    <div class="form-field__radio-group">
        <label class="form-field__radio-label">
            <input type="radio" class="form-field__radio"
                   name="taskType" value="manual"
                   x-model="task.type">
            <span>Manual</span>
        </label>
        <label class="form-field__radio-label">
            <input type="radio" class="form-field__radio"
                   name="taskType" value="fitbit"
                   x-model="task.type">
            <span>Fitbit Goal</span>
        </label>
    </div>
</div>
```

### Textarea

```html
<div class="form-field">
    <label class="form-field__label">Description</label>
    <textarea class="form-field__textarea"
              x-model="task.description"
              rows="3"
              placeholder="Additional details"></textarea>
</div>
```

### Error State

Use Alpine.js to conditionally apply error states:

```html
<div class="form-field" :class="{ 'form-field--error': errors.title }">
    <label class="form-field__label">Title</label>
    <input type="text" class="form-field__input"
           x-model="task.title">
    <span class="form-field__error" x-show="errors.title"
          x-text="errors.title"></span>
</div>
```

### Narrow Input (for numbers/dates)

Use `form-field__input--narrow` for compact number inputs:

```html
<div class="form-field">
    <label class="form-field__label">Day of Month</label>
    <input type="number" class="form-field__input form-field__input--narrow"
           x-model.number="task.day"
           min="1" max="31"
           placeholder="1-31">
</div>
```

### Icon Picker Utilities

Use shared `iconPickerUtils` from `utils.js` for icon filtering:

```javascript
// In Alpine.js component
{
    iconSearch: '',
    iconCategories: { /* categories */ },

    // Use shared utility for filtering
    get filteredIcons() {
        return window.iconPickerUtils.filterCategories(
            this.iconCategories,
            this.iconSearch
        );
    },

    // Check if search has results
    get hasResults() {
        return window.iconPickerUtils.hasVisibleIcons(
            this.iconCategories,
            this.iconSearch
        );
    }
}
```

### Mobile Considerations

All form components are mobile-optimized with:
- 48px minimum touch targets on mobile
- 16px font size to prevent iOS zoom
- Responsive layouts that stack on small screens

## Fitbit Integration Architecture

Streaklet includes optional Fitbit integration to auto-complete tasks based on fitness metrics.

### Components

**Models**:
- `fitbit_connection.py` - OAuth credentials (encrypted), profile association
- `fitbit_metric.py` - Metric configuration (steps, calories, distance, etc.)

**Services**:
- `fitbit_oauth.py` - OAuth 2.0 flow (authorization, token exchange, refresh)
- `fitbit_api.py` - API client for fetching user data
- `fitbit_sync.py` - Background sync logic (fetches metrics, auto-checks tasks)
- `fitbit_checks.py` - Task auto-completion logic based on metric thresholds
- `fitbit_scheduler.py` - APScheduler integration for periodic syncs
- `fitbit_connection.py` - Connection management

**Key Patterns**:
1. **Token Encryption**: Access/refresh tokens encrypted at rest using `app/core/encryption.py`
   - Uses Fernet symmetric encryption with `APP_SECRET_KEY`
   - Tokens decrypted only when needed for API calls
2. **Automatic Refresh**: Expired tokens auto-refreshed using refresh token
3. **Profile Isolation**: Each profile has own Fitbit connection (1:1 relationship)
4. **Sync Flow**:
   - Scheduler calls `fitbit_sync.sync_all_profiles()` periodically
   - For each profile: fetch metrics → compare to thresholds → auto-check tasks
   - Only syncs profiles with active connections

### Setup Requirements

Set these environment variables for Fitbit integration:
```bash
FITBIT_CLIENT_ID=<your_app_client_id>
FITBIT_CLIENT_SECRET=<your_app_client_secret>
FITBIT_CALLBACK_URL=http://localhost:8080/api/fitbit/callback
FITBIT_SYNC_INTERVAL_HOURS=1  # How often to sync (default: 1)
APP_SECRET_KEY=<32-byte-base64-key>  # Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

**Important**: Without `APP_SECRET_KEY`, Fitbit tokens cannot be encrypted and integration won't work.

## Token Encryption Pattern

All sensitive tokens (OAuth access/refresh tokens) are encrypted at rest:

```python
from app.core.encryption import encrypt_token, decrypt_token

# Encrypting before storage
encrypted = encrypt_token(access_token)
connection.access_token = encrypted

# Decrypting for use
access_token = decrypt_token(connection.access_token)
```

**Never store plaintext tokens in the database**. Always use encryption helpers from `app/core/encryption.py`.

## Backup and Restore

Profiles can export/import their complete data (tasks, history, checks, Fitbit connections):

- `app/services/backup.py` - Export/import logic
- Export includes: tasks, daily status, task checks, Fitbit connection/metrics
- Fitbit tokens remain encrypted in backup (require same `APP_SECRET_KEY` to restore)
- Import validates profile ownership to prevent data leakage

**API Endpoints**:
- `GET /api/profiles/{id}/export` - Download JSON backup
- `POST /api/profiles/{id}/import` - Restore from JSON

## Docker Security

The Dockerfile follows security best practices:
- Runs as non-root user (`appuser`, UID 1000)
- Data directory owned by `appuser` for write access
- In CI, tests run as `appuser` to match production environment
- Volume mounts should have proper permissions: `sudo chown -R 1000:1000 data/`

## Documentation

Documentation built with MkDocs (Material theme):
```bash
# Install mkdocs
pip install mkdocs-material

# Serve locally
mkdocs serve

# Build static site
mkdocs build
```

Docs auto-deploy to GitHub Pages via `.github/workflows/docs.yml` on pushes to main.

## Environment Variables

Set in `docker-compose.yml` or `.env`:

**Core Settings**:
- `APP_TIMEZONE` - Timezone for daily tracking (default: America/Chicago)
- `DB_PATH` - Database file location (default: /data/app.db)
- `PORT` - Application port (default: 8080)

**Security** (required for Fitbit):
- `APP_SECRET_KEY` - 32-byte base64 key for token encryption

**Fitbit Integration** (optional):
- `FITBIT_CLIENT_ID` - OAuth app client ID
- `FITBIT_CLIENT_SECRET` - OAuth app client secret
- `FITBIT_CALLBACK_URL` - OAuth callback URL (must match app settings)
- `FITBIT_SYNC_INTERVAL_HOURS` - Sync frequency in hours (default: 1)
