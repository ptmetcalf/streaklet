# Streaklet

[![CI](https://github.com/ptmetcalf/streaklet/actions/workflows/ci.yml/badge.svg)](https://github.com/ptmetcalf/streaklet/actions/workflows/ci.yml)
[![Docker](https://github.com/ptmetcalf/streaklet/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/ptmetcalf/streaklet/actions/workflows/docker-publish.yml)

A self-hosted, Dockerized daily streak tracker for maintaining consistent habits.

## Features

- **Multi-User Profiles**: Support for multiple users with completely isolated data
- **Mobile-first** daily checklist interface
- **Automatic streak tracking** based on completed days
- **Customizable tasks** with required/optional flags
- **Timezone-aware** daily tracking
- **Calendar history view** with completion stats
- **Persistent SQLite database**
- **Simple profile management** - no authentication required (designed for family/household use)

## Quick Start

### Run with Docker Compose (Development)

```bash
# Start the application
docker compose up --build

# Access at http://localhost:8080
```

### Pull from GitHub Container Registry (Production)

```bash
# Pull the latest image
docker pull ghcr.io/YOUR_USERNAME/streaklet:latest

# Run with docker compose using the published image
# (Update image in docker-compose.yml first)
docker compose up
```

## Multi-User Profiles

Streaklet supports multiple users with completely isolated data. Each profile has:
- Separate tasks
- Independent daily checks and completion tracking
- Individual streak counts
- Isolated history

### How It Works

1. **Profile Selection**: Visit `/profiles` to create or select a profile
2. **Browser Storage**: Selected profile is stored in browser localStorage
3. **Data Isolation**: All API requests include the profile context via `X-Profile-Id` header
4. **Default Tasks**: New profiles automatically get 5 starter tasks

### Profile Management

- Create profiles with custom names and colors
- Switch between profiles via the dropdown in the header
- Delete profiles (requires at least one profile to remain)
- No authentication - perfect for families or personal use on a trusted network

## Configuration

Configure via environment variables in `docker-compose.yml`:

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_TIMEZONE` | `America/Chicago` | Timezone for daily tracking |
| `DB_PATH` | `/data/app.db` | Database file location |
| `PORT` | `8080` | Application port |

## Data Persistence

The SQLite database is stored in `./data/app.db` and mounted as a Docker volume. This ensures your streak data persists across container restarts.

**Important**: Backup the `./data` directory regularly to preserve your streak history.

## Development

### Project Structure

```
app/
  main.py              # FastAPI application entry point
  core/                # Core configuration and utilities
    config.py          # Environment variables
    db.py              # Database session management
    time.py            # Timezone helpers
    profile_context.py # Profile ID dependency injection
  models/              # SQLAlchemy ORM models
    profile.py         # Profile model
    task.py            # Task model
    task_check.py      # Task check model
    daily_status.py    # Daily status model
  schemas/             # Pydantic request/response models
    profile.py         # Profile schemas
    task.py            # Task schemas
    ...
  services/            # Business logic
    profiles.py        # Profile CRUD operations
    tasks.py           # Task CRUD operations
    checks.py          # Daily check management
    streaks.py         # Streak calculation
    history.py         # Calendar history
  api/                 # API routes
    routes_profiles.py # Profile management endpoints
    routes_tasks.py    # Task endpoints
    routes_days.py     # Daily checklist endpoints
    routes_streaks.py  # Streak endpoints
    routes_history.py  # History endpoints
  web/                 # HTML templates/static files
    templates/
      base.html        # Base template with profile store
      index.html       # Today's checklist
      settings.html    # Task management
      history.html     # Calendar view
      profiles.html    # Profile management
    static/
      css/style.css    # Styles
migrations/            # Alembic database migrations
  versions/
    001_initial.py     # Initial schema
    002_add_profiles.py # Multi-user profiles
tests/                 # Pytest test suite
```

### Running Tests

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html
```

### Database Migrations

Migrations run automatically on container startup. For manual migration management:

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## API Endpoints

All endpoints (except `/api/profiles`) accept an optional `X-Profile-Id` header to specify which profile's data to access. If not provided, defaults to profile ID 1.

### Profile Management
- `GET /api/profiles` - List all profiles
- `POST /api/profiles` - Create a new profile (auto-seeds default tasks)
- `GET /api/profiles/{id}` - Get a single profile
- `PUT /api/profiles/{id}` - Update a profile
- `DELETE /api/profiles/{id}` - Delete a profile (requires at least one profile to remain)

### Tasks
- `GET /api/tasks` - List all tasks for the current profile
- `POST /api/tasks` - Create a new task
- `PUT /api/tasks/{id}` - Update a task
- `DELETE /api/tasks/{id}` - Delete a task

### Daily Checklist
- `GET /api/days/today` - Get today's checklist and status
- `PUT /api/days/{date}/checks/{task_id}` - Toggle task completion

### Streaks
- `GET /api/streak` - Get current streak information

### History
- `GET /api/history/{year}/{month}` - Get calendar data and stats for a month

### Example with Profile Header

```bash
# Get tasks for profile 2
curl -H "X-Profile-Id: 2" http://localhost:8080/api/tasks

# Check a task for profile 1
curl -X PUT -H "X-Profile-Id: 1" \
  -H "Content-Type: application/json" \
  -d '{"checked": true}' \
  http://localhost:8080/api/days/2025-12-14/checks/1
```

## Default Tasks

When creating a new profile, the following 5 starter tasks are automatically created:
1. Follow a diet (required)
2. 30 minute workout (required)
3. Read 10 pages (required)
4. 20 minutes of hobby time (required)
5. Drink 8 glasses of water (optional)

You can modify, add, or delete these tasks in the Settings screen. Each profile's tasks are completely independent.

## Homelab Deployment

### With Existing Reverse Proxy

Update your reverse proxy (nginx, Traefik, Caddy) to forward requests to `http://streaklet:8080`.

Example nginx configuration:

```nginx
location /streaklet/ {
    proxy_pass http://localhost:8080/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

### Standalone

The application is accessible directly at `http://your-server-ip:8080`.

## Tech Stack

- Python 3.12+
- FastAPI
- SQLAlchemy 2.0
- SQLite
- Alembic
- Jinja2 templates with HTMX/Alpine.js
- Docker & Docker Compose

## License

MIT
