# Streaklet - Quick Start Guide

## What Was Built

A complete, production-ready daily streak tracker with:

### Backend (FastAPI + SQLAlchemy)
- ✅ Core configuration with timezone support
- ✅ SQLite database with Alembic migrations
- ✅ Three ORM models: Task, DailyStatus, TaskCheck
- ✅ Service layer for business logic (tasks, checks, streaks)
- ✅ RESTful API endpoints
- ✅ Automatic default task seeding

### Frontend (Jinja2 + Alpine.js + HTMX)
- ✅ Mobile-first responsive design
- ✅ Home page with today's checklist
- ✅ Settings page for task management
- ✅ Real-time streak tracking
- ✅ Progress bar showing completion status

### DevOps
- ✅ Dockerfile with automatic migrations on startup
- ✅ docker-compose.yml for easy deployment
- ✅ GitHub Actions workflow for container publishing
- ✅ Health check endpoint

### Testing
- ✅ Comprehensive test suite with pytest
- ✅ Tests for tasks CRUD operations
- ✅ Tests for daily check logic
- ✅ Tests for streak calculation
- ✅ Test fixtures and database mocking

## Project Structure

```
streaklet/
├── app/
│   ├── api/              # API routes
│   │   ├── routes_tasks.py
│   │   ├── routes_days.py
│   │   └── routes_streaks.py
│   ├── core/             # Configuration & utilities
│   │   ├── config.py     # Environment variables
│   │   ├── db.py         # Database session
│   │   └── time.py       # Timezone helpers
│   ├── models/           # SQLAlchemy ORM models
│   │   ├── task.py
│   │   ├── daily_status.py
│   │   └── task_check.py
│   ├── schemas/          # Pydantic schemas
│   │   ├── task.py
│   │   ├── check.py
│   │   ├── day.py
│   │   └── streak.py
│   ├── services/         # Business logic
│   │   ├── tasks.py      # Task CRUD
│   │   ├── checks.py     # Check/completion logic
│   │   └── streaks.py    # Streak calculation
│   ├── web/              # Frontend
│   │   ├── static/css/   # Styles
│   │   └── templates/    # Jinja2 templates
│   └── main.py           # FastAPI application
├── migrations/           # Alembic migrations
├── tests/                # Test suite
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Running the Application

### Option 1: Docker (Recommended)

```bash
# Build and start
docker compose up --build

# Access at http://localhost:8080
```

### Option 2: Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

### Option 3: Using the dev script

```bash
# Run tests
./dev.sh test

# Run tests with coverage
./dev.sh test-cov

# Start development server
./dev.sh run

# Run migrations
./dev.sh migrate
```

## API Endpoints

### Tasks
- `GET /api/tasks` - List all tasks
- `POST /api/tasks` - Create task
- `PUT /api/tasks/{id}` - Update task
- `DELETE /api/tasks/{id}` - Delete task

### Days & Checks
- `GET /api/days/today` - Get today's checklist
- `PUT /api/days/{date}/checks/{task_id}` - Toggle check

### Streaks
- `GET /api/streak` - Get current streak info

### Pages
- `GET /` - Home (checklist)
- `GET /settings` - Task settings
- `GET /health` - Health check

## Environment Variables

Configure in `docker-compose.yml` or `.env`:

```bash
APP_TIMEZONE=America/Chicago  # Your timezone
DB_PATH=/data/app.db         # Database location
PORT=8080                     # Server port
```

## Default Tasks

On first run, these tasks are automatically seeded:
1. Follow a diet (Required)
2. 30 minute workout (Required)
3. 30 minute workout (Required)
4. Read 10 pages (Required)
5. 20 minutes of hobby time (Required)

## Streak Logic

- **Complete Day**: All required, active tasks are checked
- **Current Streak**: Number of consecutive completed days ending at most recent completion
- **If Today Incomplete**: Streak shows previous run (doesn't break until day ends)
- **Unchecking**: Unchecking a required task clears that day's completion

## Deploying to Your Homelab

### Step 1: Push to GitHub
```bash
git add .
git commit -m "Initial Streaklet implementation"
git push origin main
```

### Step 2: GitHub Action Runs Automatically
The workflow builds and pushes to `ghcr.io/<username>/streaklet:latest`

### Step 3: Pull on Your Server
```bash
docker pull ghcr.io/<username>/streaklet:latest
```

### Step 4: Create docker-compose.yml on Server
```yaml
version: '3.8'
services:
  streaklet:
    image: ghcr.io/<username>/streaklet:latest
    ports:
      - "8080:8080"
    volumes:
      - ./streaklet-data:/data
    environment:
      - APP_TIMEZONE=America/Chicago
    restart: unless-stopped
```

### Step 5: Start
```bash
docker compose up -d
```

## Data Backup

Your streak data lives in the SQLite database at `/data/app.db`. To backup:

```bash
# Local backup
cp ./data/app.db ./backups/app.db.$(date +%Y%m%d)

# Docker volume backup
docker compose exec streaklet cp /data/app.db /data/app.db.backup
```

## Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_streaks.py

# Run with coverage
pytest --cov=app --cov-report=html

# View coverage report
open htmlcov/index.html
```

## Troubleshooting

### Port already in use
```bash
# Change PORT in docker-compose.yml
ports:
  - "8081:8080"  # Use different host port
```

### Database locked
```bash
# Stop container, remove db, restart
docker compose down
rm -rf data/
docker compose up
```

### Migrations not running
```bash
# Run manually
docker compose exec streaklet alembic upgrade head
```

## Next Steps

- Customize default tasks in `app/services/tasks.py`
- Modify UI colors in `app/web/static/css/style.css`
- Add authentication if needed
- Set up reverse proxy (nginx, Traefik, Caddy)
- Schedule automatic backups

Enjoy your streaks! 🔥
