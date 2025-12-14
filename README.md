# Streaklet

A self-hosted, Dockerized daily streak tracker for maintaining consistent habits.

## Features

- Mobile-first daily checklist interface
- Automatic streak tracking based on completed days
- Customizable tasks with required/optional flags
- Timezone-aware daily tracking
- Persistent SQLite database
- No login required (designed for personal/LAN use)

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
  models/              # SQLAlchemy ORM models
  schemas/             # Pydantic request/response models
  services/            # Business logic
    tasks.py           # Task CRUD operations
    checks.py          # Daily check management
    streaks.py         # Streak calculation
  api/                 # API routes
    routes_tasks.py
    routes_days.py
    routes_streaks.py
  web/                 # HTML templates/static files
migrations/            # Alembic database migrations
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

- `GET /api/tasks` - List all tasks
- `POST /api/tasks` - Create a new task
- `PUT /api/tasks/{id}` - Update a task
- `DELETE /api/tasks/{id}` - Delete a task
- `GET /api/days/today` - Get today's checklist and status
- `PUT /api/days/{date}/checks/{task_id}` - Toggle task completion
- `GET /api/streak` - Get current streak information

## Default Tasks

On first run, the following tasks are seeded:
1. Follow a diet
2. 30 minute workout
3. 30 minute workout
4. Read 10 pages
5. 20 minutes of hobby time

You can modify these in the Settings screen after starting the application.

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
