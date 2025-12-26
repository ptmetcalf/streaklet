# Architecture

Understanding Streaklet's codebase structure and design patterns.

## Tech Stack

- **Backend**: Python 3.12, FastAPI
- **Database**: SQLite with SQLAlchemy 2.0 ORM
- **Frontend**: Jinja2 templates, Alpine.js, HTMX
- **Deployment**: Docker, Docker Compose

## Project Structure

```
streaklet/
├── app/
│   ├── api/                 # API route handlers
│   │   ├── routes_backup.py
│   │   ├── routes_days.py
│   │   ├── routes_fitbit.py
│   │   ├── routes_history.py
│   │   ├── routes_profiles.py
│   │   ├── routes_streaks.py
│   │   └── routes_tasks.py
│   ├── core/                # Core utilities
│   │   ├── profile_context.py   # Profile dependency injection
│   │   └── time.py             # Timezone-aware date/time
│   ├── models/              # SQLAlchemy models
│   │   ├── daily_status.py
│   │   ├── fitbit_connection.py
│   │   ├── fitbit_metrics.py
│   │   ├── profile.py
│   │   ├── task.py
│   │   └── task_check.py
│   ├── schemas/             # Pydantic schemas
│   │   ├── backup.py
│   │   ├── fitbit.py
│   │   ├── profile.py
│   │   └── task.py
│   ├── services/            # Business logic
│   │   ├── backup.py
│   │   ├── checks.py
│   │   ├── days.py
│   │   ├── fitbit/
│   │   │   ├── api.py
│   │   │   ├── checks.py
│   │   │   ├── connection.py
│   │   │   ├── encryption.py
│   │   │   ├── oauth.py
│   │   │   ├── scheduler.py
│   │   │   └── sync.py
│   │   ├── history.py
│   │   ├── profiles.py
│   │   ├── streaks.py
│   │   └── tasks.py
│   ├── web/                 # Web routes and templates
│   │   └── templates/
│   │       ├── base.html
│   │       ├── index.html
│   │       ├── settings.html
│   │       ├── fitbit.html
│   │       ├── history.html
│   │       └── profiles.html
│   ├── database.py          # Database session management
│   ├── main.py              # FastAPI app entry point
│   └── startup.py           # Application startup logic
├── migrations/              # Alembic database migrations
│   └── versions/
├── tests/                   # Pytest test suite
├── data/                    # SQLite database (gitignored)
├── docs/                    # MkDocs documentation
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── mkdocs.yml
└── README.md
```

## Architectural Patterns

### 1. Multi-User Profile Isolation

**Core Concept**: Every piece of data belongs to a specific profile (user).

**Implementation Layers**:

**A. Database Level** (Foreign Keys)
```python
# All tables include user_id FK
class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("profiles.id"), nullable=False, index=True)
    # ... other fields
```

**B. API Level** (HTTP Headers)
```python
# Frontend sends X-Profile-Id with every request
const response = await fetchWithProfile('/api/tasks');
// fetchWithProfile() adds: headers: { 'X-Profile-Id': profileId }
```

**C. Dependency Injection** (FastAPI)
```python
# Extract profile ID from header
def get_profile_id(x_profile_id: int | None = Header(default=None)) -> int:
    return x_profile_id or 1

# Use in routes
@router.get("/api/tasks")
def get_tasks(
    db: Session = Depends(get_db),
    profile_id: int = Depends(get_profile_id)  # Injected
):
    return task_service.list_tasks(db, profile_id)
```

**D. Service Layer** (Data Filtering)
```python
# All service functions accept profile_id
def list_tasks(db: Session, profile_id: int):
    return db.query(Task).filter(
        Task.user_id == profile_id  # Always filter by profile
    ).all()
```

**Key Files**:
- `app/core/profile_context.py` - Dependency injection
- `app/web/templates/base.html` - `fetchWithProfile()` helper
- All service functions - Accept `profile_id` parameter

### 2. Timezone-Aware Date Handling

**Problem**: Users in different timezones expect "today" to match their local date.

**Solution**: All date operations use configured timezone.

**Implementation**:
```python
# app/core/time.py
from zoneinfo import ZoneInfo

def get_timezone() -> ZoneInfo:
    return ZoneInfo(os.getenv("APP_TIMEZONE", "America/Chicago"))

def get_today() -> date:
    """Returns today's date in configured timezone"""
    return datetime.now(get_timezone()).date()

def get_now() -> datetime:
    """Returns current datetime in configured timezone"""
    return datetime.now(get_timezone())
```

**Rule**: NEVER use `date.today()` or `datetime.now()` directly. Always use helpers.

**Key Files**:
- `app/core/time.py` - Timezone utilities
- All services - Use `get_today()` and `get_now()`

### 3. Daily Completion Logic

**Concept**: A day is complete when ALL required active tasks are checked.

**Flow**:
1. User checks/unchecks task → API call
2. `check_service.update_task_check()` updates check
3. `recompute_daily_completion()` automatically called:
   - Queries all required active tasks for profile
   - Checks if all are completed
   - Updates `DailyStatus` with `completed_at` timestamp
4. Streak calculation reads `DailyStatus` for consecutive days

**Implementation**:
```python
# app/services/checks.py
def recompute_daily_completion(
    db: Session,
    date: date,
    profile_id: int
):
    """Recompute if day is complete based on all required tasks"""
    required_tasks = db.query(Task).filter(
        Task.user_id == profile_id,
        Task.required == True,
        Task.active == True
    ).all()

    if not required_tasks:
        return

    checks = db.query(TaskCheck).filter(
        TaskCheck.date == date,
        TaskCheck.user_id == profile_id
    ).all()

    checked_task_ids = {c.task_id for c in checks if c.checked}
    required_task_ids = {t.id for t in required_tasks}

    day_complete = required_task_ids.issubset(checked_task_ids)

    daily_status = get_or_create_daily_status(db, date, profile_id)
    daily_status.completed_at = get_now() if day_complete else None
    db.commit()
```

**Key Files**:
- `app/services/checks.py` - Completion logic
- `app/models/daily_status.py` - Completion timestamp storage

### 4. Streak Calculation

**Algorithm**: Count consecutive days backward from today (or most recent completion).

**Rules**:
- If today is complete, streak includes today
- If today is incomplete, streak ends at most recent completion
- Break on any day with no completion

**Implementation**:
```python
# app/services/streaks.py
def calculate_current_streak(db: Session, profile_id: int) -> int:
    today = get_today()

    # Check if today is complete
    today_status = db.query(DailyStatus).filter(
        DailyStatus.date == today,
        DailyStatus.user_id == profile_id,
        DailyStatus.completed_at.isnot(None)
    ).first()

    # Start from today or yesterday
    check_date = today if today_status else today - timedelta(days=1)
    streak = 0

    # Count backwards
    while True:
        status = db.query(DailyStatus).filter(
            DailyStatus.date == check_date,
            DailyStatus.user_id == profile_id,
            DailyStatus.completed_at.isnot(None)
        ).first()

        if not status:
            break  # Streak ends

        streak += 1
        check_date -= timedelta(days=1)

    return streak
```

**Key Files**:
- `app/services/streaks.py` - Streak calculation
- `app/models/daily_status.py` - Completion records

### 5. Fitbit Integration

**Architecture**: OAuth 2.0 → Token Storage → Scheduled Sync → Auto-Complete Tasks

**Components**:

**A. OAuth Flow** (`app/services/fitbit/oauth.py`)
1. Generate auth URL with state token
2. User authorizes on Fitbit
3. Callback receives code
4. Exchange code for access + refresh tokens
5. Encrypt and store tokens

**B. Token Encryption** (`app/services/fitbit/encryption.py`)
```python
from cryptography.fernet import Fernet

def encrypt_token(token: str) -> str:
    key = get_encryption_key()  # From APP_SECRET_KEY
    f = Fernet(key)
    return f.encrypt(token.encode()).decode()

def decrypt_token(encrypted: str) -> str:
    key = get_encryption_key()
    f = Fernet(key)
    return f.decrypt(encrypted.encode()).decode()
```

**C. API Client** (`app/services/fitbit/api.py`)
- Fetches activity, sleep, heart rate data
- Handles rate limiting (150 requests/hour)
- Auto-refreshes expired tokens

**D. Scheduled Sync** (`app/services/fitbit/scheduler.py`)
```python
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(
    sync_all_profiles_job,
    'interval',
    hours=1,  # Sync every hour
    id='fitbit_sync'
)
```

**E. Auto-Complete** (`app/services/fitbit/checks.py`)
```python
def evaluate_and_apply_auto_checks(db: Session, profile_id: int, date: date):
    """Auto-check tasks based on Fitbit metrics"""
    tasks = db.query(Task).filter(
        Task.user_id == profile_id,
        Task.fitbit_auto_check == True
    ).all()

    metrics = get_fitbit_metrics_for_date(db, profile_id, date)

    for task in tasks:
        if evaluate_goal(metrics, task.fitbit_metric_type,
                        task.fitbit_goal_operator, task.fitbit_goal_value):
            # Goal met → check task
            update_task_check(db, date, task.id, True, profile_id)
        else:
            # Goal not met → uncheck task
            update_task_check(db, date, task.id, False, profile_id)
```

**Key Files**:
- `app/services/fitbit/` - All Fitbit logic
- `app/models/fitbit_connection.py` - OAuth tokens
- `app/models/fitbit_metrics.py` - Cached metrics

### 6. Client-Side Data Fetching

**Pattern**: Templates render skeleton, Alpine.js fetches data via API.

**Implementation**:
```html
<!-- app/web/templates/index.html -->
<div x-data="dailyView" x-init="await loadData()">
    <template x-if="loading">
        <p>Loading...</p>
    </template>

    <template x-if="!loading">
        <div x-for="task in tasks" :key="task.id">
            <span x-text="task.title"></span>
        </div>
    </template>
</div>

<script>
document.addEventListener('alpine:init', () => {
    Alpine.data('dailyView', () => ({
        tasks: [],
        loading: true,

        async loadData() {
            const response = await fetchWithProfile('/api/tasks');
            this.tasks = await response.json();
            this.loading = false;
        }
    }));
});
</script>
```

**Benefits**:
- Separation of concerns (templates ≠ data)
- Profile switching without page reload
- Progressive enhancement
- API-first design

**Key Files**:
- `app/web/templates/base.html` - Alpine.js setup + helpers
- All templates - Use `x-data` + `x-init="loadData()"`

## Database Schema

### Core Tables

**profiles**
```sql
CREATE TABLE profiles (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    color TEXT NOT NULL
);
```

**tasks**
```sql
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,  -- FK to profiles
    title TEXT NOT NULL,
    description TEXT,
    required BOOLEAN DEFAULT TRUE,
    active BOOLEAN DEFAULT TRUE,
    fitbit_auto_check BOOLEAN DEFAULT FALSE,
    fitbit_metric_type TEXT,
    fitbit_goal_operator TEXT,
    fitbit_goal_value REAL,
    FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE
);
```

**task_checks**
```sql
CREATE TABLE task_checks (
    id INTEGER PRIMARY KEY,
    task_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    date DATE NOT NULL,
    checked BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE,
    UNIQUE (task_id, date, user_id)
);
```

**daily_status**
```sql
CREATE TABLE daily_status (
    date DATE NOT NULL,
    user_id INTEGER NOT NULL,
    completed_at TIMESTAMP,
    PRIMARY KEY (date, user_id),
    FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE
);
```

### Relationships

- `Profile` → `Tasks` (one-to-many)
- `Task` → `TaskChecks` (one-to-many)
- `Profile` → `DailyStatus` (one-to-many)
- `Profile` → `FitbitConnection` (one-to-one)
- `Profile` → `FitbitMetrics` (one-to-many)

## API Design

### RESTful Conventions

- `GET /api/resources` - List
- `GET /api/resources/:id` - Get single
- `POST /api/resources` - Create
- `PUT /api/resources/:id` - Update
- `DELETE /api/resources/:id` - Delete

### Profile Context

All endpoints accept `X-Profile-Id` header:
```bash
curl -H "X-Profile-Id: 2" http://localhost:8080/api/tasks
```

Defaults to profile 1 if omitted.

### Response Format

**Success:**
```json
{
  "id": 1,
  "title": "Task name"
}
```

**Error:**
```json
{
  "detail": "Error message"
}
```

## Testing Strategy

### Test Structure

```
tests/
├── test_backup.py       # Backup/restore
├── test_daily_checks.py # Check logic
├── test_days.py         # Daily API
├── test_fitbit_*.py     # Fitbit (oauth, api, sync, etc.)
├── test_history.py      # Calendar/history
├── test_profiles.py     # Profiles
├── test_streaks.py      # Streak calculation
├── test_tasks.py        # Tasks
└── conftest.py          # Fixtures
```

### Fixtures

**Critical:** `sample_profiles` must be created before other fixtures.

```python
# conftest.py
@pytest.fixture
def sample_profiles(test_db):
    """Create profiles first - required for all other fixtures"""
    profiles = [
        Profile(id=1, name="Test User", color="#3b82f6"),
        Profile(id=2, name="Another User", color="#10b981")
    ]
    test_db.add_all(profiles)
    test_db.commit()
    return profiles

@pytest.fixture
def sample_tasks(test_db, sample_profiles):  # Depends on sample_profiles
    tasks = [Task(user_id=1, title="Task 1", ...)]
    test_db.add_all(tasks)
    test_db.commit()
    return tasks
```

### Test Patterns

**Service tests:**
```python
def test_create_task(test_db, sample_profiles):
    task = task_service.create_task(
        test_db,
        profile_id=1,
        title="New Task",
        required=True
    )
    assert task.id is not None
    assert task.user_id == 1
```

**API tests:**
```python
def test_api_create_task(client, sample_profiles):
    response = client.post(
        "/api/tasks",
        headers={"X-Profile-Id": "1"},
        json={"title": "New Task", "required": True}
    )
    assert response.status_code == 200
```

## Deployment

### Docker Multi-Stage Build

**Stage 1: Builder**
- Install build dependencies (gcc)
- Install Python packages

**Stage 2: Runtime**
- Copy packages from builder
- No build tools (smaller, more secure)
- Run as non-root user (uid 1000)

**Security Features**:
- Non-root execution
- Minimal attack surface
- Health checks
- No unnecessary packages

### Environment Variables

See [Configuration](../getting-started/configuration.md) for full reference.

## Performance Considerations

### SQLite Optimization

- Indexed foreign keys (`user_id`)
- Composite primary keys where appropriate
- WAL mode enabled (better concurrency)

### Caching

- Service worker caches static assets
- Browser localStorage for profile selection
- Fitbit metrics cached in database

### Scalability Limits

SQLite is suitable for:
- Families/households (< 10 users)
- < 100,000 records
- Single-server deployment

For larger deployments, consider PostgreSQL migration (future feature).

## Security

### Authentication

**None built-in** - Designed for trusted networks.

Add authentication at reverse proxy level for public access.

### Token Encryption

Fitbit tokens encrypted with AES-256 using `APP_SECRET_KEY`.

### SQL Injection

Protected by SQLAlchemy ORM parameterized queries.

### XSS Protection

- Jinja2 auto-escapes templates
- Alpine.js uses safe DOM manipulation

## Future Architecture Considerations

### Planned Features

- **Multi-database support**: PostgreSQL option
- **Real-time updates**: WebSockets for live sync
- **Mobile apps**: React Native or Flutter
- **Plugin system**: Custom integrations
- **Export formats**: CSV, PDF reports

### Technical Debt

- **No caching layer**: Consider Redis for scaling
- **No job queue**: Consider Celery for background tasks
- **Timezone per profile**: Currently global timezone
- **API versioning**: No version prefix yet

## Contributing

See [Contributing Guide](contributing.md) for:
- Code style guidelines
- Commit conventions
- PR process
- Testing requirements

## Learn More

- [Local Setup](local-setup.md) - Development environment
- [API Reference](../api/endpoints.md) - Complete API docs
- [Contributing](contributing.md) - How to contribute
