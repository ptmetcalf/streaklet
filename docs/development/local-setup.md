# Local Development Setup

Set up Streaklet for local development.

## Prerequisites

- **Python 3.12+**
- **Git**
- **pip** (Python package manager)
- **Docker** (optional, for testing containers)

## Clone Repository

```bash
git clone https://github.com/ptmetcalf/streaklet.git
cd streaklet
```

## Virtual Environment Setup

**Create virtual environment:**
```bash
python3 -m venv .venv
```

**Activate virtual environment:**
```bash
# Linux/macOS
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Windows (CMD)
.venv\Scripts\activate.bat
```

**Verify activation:**
```bash
which python  # Should show .venv/bin/python
```

## Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Development tools:**
```bash
pip install ruff  # Linter
```

## Database Setup

**Run migrations:**
```bash
alembic upgrade head
```

This creates `data/app.db` with the schema.

**Verify database:**
```bash
ls -lh data/app.db
```

## Environment Configuration

Create `.env` file (optional):
```bash
# .env
APP_TIMEZONE=America/Chicago
DB_PATH=data/app.db
PORT=8080

# Optional: Fitbit integration
# FITBIT_CLIENT_ID=your_client_id
# FITBIT_CLIENT_SECRET=your_client_secret
# APP_SECRET_KEY=your_secure_random_key
```

Load environment variables:
```bash
export $(cat .env | xargs)
```

## Running the Development Server

### Using dev.sh (Recommended)

```bash
./dev.sh run
```

This starts uvicorn with auto-reload enabled.

### Manual uvicorn

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

**Options:**
- `--reload` - Auto-restart on code changes
- `--host 0.0.0.0` - Accept connections from any IP
- `--port 8080` - Port to listen on

### Access the Application

Open browser to: `http://localhost:8080`

## Running Tests

### All Tests

```bash
./dev.sh test
# Or manually:
python -m pytest tests/ -v
```

### With Coverage

```bash
./dev.sh test-cov
# Or manually:
python -m pytest tests/ --cov=app --cov-report=html --cov-report=term
```

View HTML coverage report:
```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Single Test File

```bash
python -m pytest tests/test_tasks.py -v
```

### Single Test Function

```bash
python -m pytest tests/test_tasks.py::test_create_task -v
```

### Watch Mode (Requires pytest-watch)

```bash
pip install pytest-watch
ptw tests/ -- -v
```

## Linting

### Check Code

```bash
./dev.sh lint
# Or manually:
ruff check app/ tests/
```

### Auto-Fix Issues

```bash
ruff check app/ tests/ --fix
```

### CI-Style Check (Critical Errors Only)

```bash
ruff check app/ tests/ --select=E9,F63,F7,F82
```

This is what CI runs. Must pass for PRs.

## Database Migrations

### Create New Migration

```bash
./dev.sh migrate-new "description"
# Or manually:
alembic revision --autogenerate -m "add new column"
```

### Apply Migrations

```bash
./dev.sh migrate
# Or manually:
alembic upgrade head
```

### Rollback Migration

```bash
alembic downgrade -1
```

### View Migration History

```bash
alembic history
```

### View Current Version

```bash
alembic current
```

## Docker Development

### Build Image

```bash
docker build -t streaklet:dev .
```

### Run Container

```bash
docker run -d \
  --name streaklet-dev \
  -p 8080:8080 \
  -v ./data:/data \
  -e APP_TIMEZONE=America/Chicago \
  streaklet:dev
```

### Run Tests in Docker

```bash
docker build -t streaklet:test .
docker run --rm --entrypoint "" --user appuser streaklet:test \
  sh -c "PYTHONPATH=. python -m pytest tests/ -v"
```

### Docker Compose Development

```bash
docker compose up --build
```

Edit files locally; rebuild when needed:
```bash
docker compose down
docker compose up --build -d
```

## IDE Configuration

### VS Code

**Recommended Extensions:**
- Python
- Pylance
- Ruff

**settings.json:**
```json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "none",
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll": true
    }
  }
}
```

### PyCharm

**Configure interpreter:**
1. Settings → Project → Python Interpreter
2. Add Interpreter → Existing environment
3. Select `.venv/bin/python`

**Enable Ruff:**
1. Settings → Tools → External Tools
2. Add tool: `ruff check $FilePath$`

## Debugging

### VS Code Debug Configuration

**.vscode/launch.json:**
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app.main:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8080"
      ],
      "jinja": true,
      "justMyCode": true,
      "env": {
        "APP_TIMEZONE": "America/Chicago"
      }
    },
    {
      "name": "Pytest",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": [
        "tests/",
        "-v"
      ],
      "justMyCode": true
    }
  ]
}
```

### Python Debugger (pdb)

Add breakpoint in code:
```python
import pdb; pdb.set_trace()
```

Or use built-in `breakpoint()`:
```python
breakpoint()
```

### Print Debugging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)
logger.debug(f"Variable value: {variable}")
```

## Common Development Tasks

### Reset Database

```bash
rm data/app.db
alembic upgrade head
```

### Seed Test Data

Create a seed script (e.g., `seed.py`):
```python
from app.database import SessionLocal
from app.services import profiles, tasks

db = SessionLocal()

# Create profiles
profile = profiles.create_profile(db, name="Test User", color="#3b82f6")

# Create tasks
tasks.create_task(db, profile_id=profile.id, title="Test Task", required=True, active=True)

db.close()
```

Run it:
```bash
python seed.py
```

### Clear Cache

```bash
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```

### Update Dependencies

```bash
pip list --outdated
pip install --upgrade package-name
pip freeze > requirements.txt
```

## Troubleshooting

### Import Errors

Ensure `PYTHONPATH` is set:
```bash
export PYTHONPATH=.
python -m pytest tests/
```

### Database Locked

SQLite locks when accessed by multiple processes:
```bash
# Kill all Python processes
pkill -f python
rm data/app.db-journal  # Remove lock file
```

### Port Already in Use

Find process using port 8080:
```bash
# Linux/macOS
lsof -i :8080
kill -9 <PID>

# Windows
netstat -ano | findstr :8080
taskkill /PID <PID> /F
```

### Virtual Environment Not Activating

Recreate it:
```bash
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Tests Failing

1. Check database exists: `ls data/app.db`
2. Run migrations: `alembic upgrade head`
3. Clear pytest cache: `rm -rf .pytest_cache`
4. Check environment variables: `env | grep APP_`

## Git Workflow

See [Contributing Guide](contributing.md) for detailed Git workflow and commit conventions.

Quick reference:
```bash
# Create feature branch
git checkout -b feature/my-feature

# Make changes, commit with conventional commits
git add .
git commit -m "feat: add new feature"

# Push and create PR
git push origin feature/my-feature
```

## Next Steps

- [Contributing Guide](contributing.md) - How to contribute
- [Architecture](architecture.md) - Codebase structure
- [API Reference](../api/endpoints.md) - API documentation
