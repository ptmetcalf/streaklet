# Streaklet

[![CI](https://github.com/ptmetcalf/streaklet/actions/workflows/ci.yml/badge.svg)](https://github.com/ptmetcalf/streaklet/actions/workflows/ci.yml)
[![Docker](https://github.com/ptmetcalf/streaklet/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/ptmetcalf/streaklet/actions/workflows/docker-publish.yml)
[![codecov](https://codecov.io/gh/ptmetcalf/streaklet/branch/main/graph/badge.svg)](https://codecov.io/gh/ptmetcalf/streaklet)

A self-hosted, Dockerized daily streak tracker for maintaining consistent habits.

## Features

- **Multi-User Profiles**: Support for multiple users with completely isolated data
- **Fitbit Integration**: Automatic task completion based on Fitbit metrics (steps, sleep, heart rate, etc.)
- **Progressive Web App (PWA)**: Install on mobile devices for native app-like experience
- **Offline Support**: Service worker caching for offline functionality
- **Mobile-first** daily checklist interface
- **Automatic streak tracking** based on completed days
- **Customizable tasks** with required/optional flags
- **Timezone-aware** daily tracking
- **Calendar history view** with completion stats
- **Backup & restore** functionality for data protection
- **Persistent SQLite database**
- **Simple profile management** - no authentication required (designed for family/household use)

## Quick Start

### Run with Docker Compose (Development)

```bash
# Start the application
docker build -t streaklet .
docker compose up --no-build

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

## Fitbit Integration

Streaklet can automatically complete tasks based on your Fitbit data. Connect your Fitbit account and configure tasks to auto-complete when you hit specific metric goals (steps, sleep, active minutes, etc.).

### How It Works

1. **Connect Fitbit**: Navigate to Settings and click "Connect Fitbit" to authorize via OAuth 2.0
2. **Configure Tasks**: Enable "Fitbit Auto-Check" on any task and set metric type + goal
3. **Automatic Sync**: Data syncs hourly and auto-completes tasks when goals are met
4. **Manual Sync**: Click "Sync Now" in Settings to immediately fetch latest data

### Setting Up a Task with Fitbit

When creating or editing a task:

1. Enable **Fitbit Auto-Check**
2. Select a **Metric Type**:
   - `steps` - Daily step count
   - `sleep_minutes` - Total sleep duration in minutes
   - `active_minutes` - Active zone minutes (light + moderate + very active)
   - `calories_burned` - Total calories burned
   - `distance_km` - Distance traveled in kilometers
   - `floors_climbed` - Floors climbed
   - `resting_heart_rate` - Resting heart rate (BPM)
   - `heart_rate_zones_cardio` - Minutes in cardio zone
   - `heart_rate_zones_fat_burn` - Minutes in fat burn zone
   - `heart_rate_zones_peak` - Minutes in peak zone

3. Set **Goal Operator**:
   - `>=` - Greater than or equal to (most common, e.g., "at least 10,000 steps")
   - `<=` - Less than or equal to (e.g., "no more than 400 minutes sleep")
   - `==` - Exactly equal to (rare use case)

4. Enter **Goal Value** (numeric value to compare against)

**Example**: Task "Walk 10,000 steps"
- Metric Type: `steps`
- Goal Operator: `>=`
- Goal Value: `10000`

When your Fitbit reports 10,000+ steps, this task auto-completes for the day.

### Fitbit Connection Management

#### Connecting

1. Go to **Settings** page
2. Click **Connect Fitbit** button
3. Authorize Streaklet in the Fitbit OAuth flow
4. You'll be redirected back with connection confirmed

#### Status

The Settings page shows:
- Connection status (Connected/Not Connected)
- Fitbit user display name
- Last sync time and status
- Manual sync button

#### Disconnecting

Click **Disconnect Fitbit** to:
- Revoke OAuth tokens
- Delete all stored Fitbit metrics
- Disable Fitbit auto-check on all tasks

### Data Syncing

**Automatic Sync**: Runs every hour to fetch yesterday and today's data

**Manual Sync**: Click "Sync Now" in Settings to immediately:
1. Fetch latest Fitbit metrics for today and yesterday
2. Store metrics in local database
3. Auto-complete tasks that meet their goals

**Historical Data**: Access the Fitbit Metrics page to view charts of historical data (last 30 days by default)

### Privacy and Data Storage

- OAuth tokens stored encrypted in SQLite database
- Fitbit data stored locally per profile (complete data isolation)
- No third-party data sharing
- Disconnect anytime to delete all Fitbit data

### Fitbit API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/fitbit/connect` | GET | Initiate OAuth flow |
| `/api/fitbit/callback` | GET | OAuth callback (automatic) |
| `/api/fitbit/connection` | GET | Get connection status |
| `/api/fitbit/connection` | DELETE | Disconnect and delete data |
| `/api/fitbit/sync` | POST | Trigger manual sync |
| `/api/fitbit/sync-status` | GET | Get last sync time and status |
| `/api/fitbit/metrics` | GET | Get metrics for date range |
| `/api/fitbit/daily-summary` | GET | Get all metrics for specific date |
| `/api/fitbit/metrics/history` | GET | Get historical metrics for charting |

### Requirements

To use Fitbit integration, you must configure environment variables:

```bash
FITBIT_CLIENT_ID=your_client_id
FITBIT_CLIENT_SECRET=your_client_secret
FITBIT_REDIRECT_URI=http://your-domain:8080/api/fitbit/callback
APP_SECRET_KEY=your_secret_key_for_token_encryption
```

Register your application at [dev.fitbit.com](https://dev.fitbit.com) to obtain credentials.

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

## Progressive Web App (PWA)

Streaklet is a fully installable Progressive Web App that works on mobile devices and desktops.

### Features

- **Install to Home Screen**: Add Streaklet to your device's home screen for quick access
- **Offline Support**: Service worker caches data for offline functionality
- **Native App Experience**: Runs in standalone mode without browser UI
- **Automatic Updates**: Service worker automatically updates when new versions are deployed

### Installing on Mobile

#### iOS (iPhone/iPad)

1. Open Streaklet in Safari
2. Tap the Share button (square with arrow)
3. Scroll down and tap "Add to Home Screen"
4. Tap "Add" in the top right

#### Android (Chrome)

1. Open Streaklet in Chrome
2. Tap the three-dot menu
3. Select "Add to Home screen" or "Install app"
4. Tap "Install" in the popup

### Installing on Desktop

#### Chrome/Edge

1. Open Streaklet in Chrome or Edge
2. Look for the install icon (+) in the address bar
3. Click "Install" in the popup

#### Other Browsers

Most modern browsers support PWA installation. Look for an install prompt or check the browser menu.

### Offline Functionality

The service worker caches:
- Static assets (CSS, HTML)
- API responses for read operations
- App icons and manifest

When offline:
- Previously loaded pages will still work
- Recent task data will be accessible
- Task completion will work with cached data
- Changes sync automatically when back online

### Testing PWA Installation

To verify PWA features are working:

```bash
# Check manifest
curl http://localhost:8080/static/manifest.json

# Check service worker
curl http://localhost:8080/static/sw.js

# Check icons
curl -I http://localhost:8080/static/icons/icon-192x192.png
```

## Backup & Data Import/Export

Streaklet includes built-in backup and restore functionality to protect your data and enable migration between instances.

### Features

- **Export individual profiles** or all profiles at once
- **JSON format** - human-readable and editable
- **Import modes**:
  - **Replace**: Delete existing data and replace with imported data
  - **Merge**: Keep existing data and add imported data (skips duplicates)
- **Complete data export**: Includes profile info, tasks, check history, and daily completion records

### Using the UI

#### Export a Profile

1. Navigate to the **Profiles** page
2. Click the **Export** button on the profile card
3. A JSON file will be downloaded with the profile's data
4. Store this file in a safe location

#### Import a Profile

1. Navigate to the **Profiles** page
2. Click the **Import** button on the profile card
3. Select the JSON backup file
4. Choose import mode:
   - **OK** = Replace (deletes existing data)
   - **Cancel** = Merge (keeps existing data)
5. The profile data will be imported

#### Export All Profiles

1. Navigate to the **Profiles** page
2. Click **Export All Profiles** at the top
3. A JSON file with all profiles will be downloaded

#### Import All Profiles

1. Navigate to the **Profiles** page
2. Click **Import All Profiles** at the top
3. Select the JSON backup file
4. Choose import mode (Replace or Merge)
5. All profiles will be imported

### Using the API

#### Export Single Profile

```bash
# Download profile 1 data
curl -O http://localhost:8080/api/profiles/1/export
```

#### Import Single Profile

```bash
# Replace mode (delete existing data)
curl -X POST http://localhost:8080/api/profiles/1/import \
  -F "file=@backup.json" \
  -F "mode=replace"

# Merge mode (keep existing data)
curl -X POST http://localhost:8080/api/profiles/1/import \
  -F "file=@backup.json" \
  -F "mode=merge"
```

#### Export All Profiles

```bash
curl -O http://localhost:8080/api/profiles/export/all
```

#### Import All Profiles

```bash
curl -X POST http://localhost:8080/api/profiles/import/all \
  -F "file=@all_profiles_backup.json" \
  -F "mode=replace"
```

### Backup File Format

Single profile export:
```json
{
  "version": "1.0",
  "export_date": "2025-12-14T22:30:00Z",
  "profile": {
    "id": 1,
    "name": "John",
    "color": "#3b82f6"
  },
  "tasks": [...],
  "task_checks": [...],
  "daily_status": [...]
}
```

All profiles export:
```json
{
  "version": "1.0",
  "export_date": "2025-12-14T22:30:00Z",
  "profiles": [
    {
      "version": "1.0",
      "export_date": "2025-12-14T22:30:00Z",
      "profile": {...},
      "tasks": [...],
      "task_checks": [...],
      "daily_status": [...]
    }
  ]
}
```

### Best Practices

- **Regular backups**: Export your data regularly (weekly or monthly)
- **Before updates**: Always export before updating Streaklet
- **Multiple locations**: Store backups in multiple locations (local + cloud)
- **Test restores**: Periodically test importing backups to verify they work
- **Version control**: Keep dated backup files (e.g., `streaklet_john_2025-12-14.json`)

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

### Backup & Import
- `GET /api/profiles/{id}/export` - Export profile data as JSON
- `POST /api/profiles/{id}/import` - Import profile data from JSON file
- `GET /api/profiles/export/all` - Export all profiles as JSON
- `POST /api/profiles/import/all` - Import all profiles from JSON file

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
