# Quick Start Guide

Get up and running with Streaklet in 5 minutes.

## 1. Start Streaklet

Choose your preferred method:

### Option 1: Docker (Recommended)

```bash
docker run -d -p 8080:8080 -v ./data:/data ghcr.io/ptmetcalf/streaklet:latest
```

### Option 2: Local Development

**Prerequisites:** Python 3.12+, `python3-venv` (Ubuntu/Debian: `apt install python3.12-venv`)

```bash
# Clone repository
git clone https://github.com/ptmetcalf/streaklet.git
cd streaklet

# Create data directory
mkdir -p data

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# Windows: .venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run database migrations (use local path)
DB_PATH=data/app.db alembic upgrade head

# Start development server (use local path)
DB_PATH=data/app.db uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

See [Local Development Setup](../development/local-setup.md) for detailed instructions.

## 2. Open in Browser

Navigate to `http://localhost:8080`

## 3. Create Your Profile

You'll be redirected to the Profiles page. A "Default Profile" is automatically created.

- Click **Edit** to customize the name and color
- Or click **Add Profile** to create additional profiles for family members

## 4. Add Your Tasks

Click **Settings** in the bottom navigation and:

1. Edit the default tasks or create your own
2. Mark tasks as **Required** (must complete for streak) or optional
3. Drag to reorder tasks
4. Save changes

## 5. Start Tracking

Click **Checklist** to return to today's view and start checking off tasks!

- Tap tasks to mark them complete
- See your progress bar fill up
- Complete all required tasks to continue your streak

## Understanding Streaks

- **Day 1**: Complete all required tasks
- **Streak continues**: Keep completing all required tasks daily
- **Streak breaks**: Miss any required task on any day
- **Today incomplete**: Streak shows Day 1 until today is complete

## Multi-User Setup

Each family member can have their own profile:

1. Go to **Profiles** page
2. Click **Add Profile**
3. Choose name and color
4. Each profile gets independent:
   - Tasks
   - Check history
   - Streak count
   - Calendar

## Next Steps

- [Enable Fitbit Integration](../features/fitbit.md) - Auto-complete tasks
- [Install as PWA](../features/pwa.md) - Add to home screen
- [Configure Settings](configuration.md) - Customize timezone and more
