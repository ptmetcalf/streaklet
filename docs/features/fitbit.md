# Fitbit Integration

Streaklet integrates with Fitbit to automatically complete tasks based on your fitness metrics.

## Overview

The Fitbit integration allows you to:

- **Auto-complete tasks** based on daily metrics (steps, sleep, heart rate, etc.)
- **View metrics** directly in Streaklet
- **Track progress** toward fitness goals
- **Historical sync** - backfill up to 30 days of data

## Setup

### 1. Register a Fitbit Application

Before connecting Fitbit, you need to register an application with Fitbit:

1. Go to [dev.fitbit.com](https://dev.fitbit.com/apps)
2. Click **"Register An App"**
3. Fill in the application details:
   - **Application Name**: Streaklet (or your preferred name)
   - **Description**: Personal habit tracker
   - **Application Website**: `http://localhost:8080` (or your domain)
   - **Organization**: Your name
   - **Organization Website**: `http://localhost:8080` (or your domain)
   - **OAuth 2.0 Application Type**: **Personal**
   - **Callback URL**: `http://localhost:8080/api/fitbit/callback` (important!)
   - **Default Access Type**: **Read Only**
4. Agree to terms and click **Register**
5. Note your **Client ID** and **Client Secret**

### 2. Configure Streaklet

Add your Fitbit credentials to your environment:

**Docker Compose:**
```yaml
environment:
  - FITBIT_CLIENT_ID=your_client_id_here
  - FITBIT_CLIENT_SECRET=your_client_secret_here
  - APP_SECRET_KEY=your_random_32_character_secret
```

**Direct Docker:**
```bash
docker run -d \
  -p 8080:8080 \
  -v ./data:/data \
  -e FITBIT_CLIENT_ID=your_client_id_here \
  -e FITBIT_CLIENT_SECRET=your_client_secret_here \
  -e APP_SECRET_KEY=your_random_32_character_secret \
  ghcr.io/ptmetcalf/streaklet:latest
```

**Important:** `APP_SECRET_KEY` is used to encrypt Fitbit tokens. Use a secure random 32+ character string.

### 3. Connect Your Fitbit Account

1. Navigate to **Settings** in Streaklet
2. Click **"Connect Fitbit"** in the Fitbit section
3. Log in to your Fitbit account and authorize Streaklet
4. You'll be redirected back with a success message

## Auto-Completing Tasks

Tasks can be configured to auto-complete when Fitbit metrics meet certain conditions.

### Creating Auto-Check Tasks

When creating or editing a task, enable Fitbit auto-check:

1. Check **"Enable Fitbit Auto-Check"**
2. Select a **Metric Type**:
   - `steps` - Daily step count
   - `distance` - Distance in miles
   - `floors` - Floors climbed
   - `calories` - Calories burned
   - `active_minutes` - Active minutes
   - `sleep_minutes` - Total sleep time
   - `resting_heart_rate` - Resting heart rate (BPM)
3. Choose a **Goal Operator**:
   - `>=` - Greater than or equal (most common)
   - `<=` - Less than or equal
   - `==` - Exactly equal
4. Set **Goal Value** (numeric)

**Example:** "Walk 10,000 steps"
- Metric: `steps`
- Operator: `>=`
- Goal: `10000`

### How Auto-Check Works

1. **Automatic Sync**: Streaklet syncs with Fitbit every hour (configurable)
2. **Goal Evaluation**: When metrics are synced, tasks are evaluated
3. **Auto-Complete**: If the goal is met, the task is automatically checked
4. **Auto-Uncheck**: If you fall below the goal, the task is unchecked

### Manual Sync

Force a sync at any time:

- Click **"Sync Now"** on the Fitbit settings page
- Or use the API: `POST /api/fitbit/sync`

## Available Metrics

| Metric | Description | Example Use Case |
|--------|-------------|------------------|
| `steps` | Total steps for the day | Walk 10,000 steps |
| `distance` | Miles traveled | Walk 5 miles |
| `floors` | Floors climbed | Climb 10 floors |
| `calories` | Calories burned | Burn 2,500 calories |
| `active_minutes` | Very active + fairly active minutes | 30 active minutes |
| `sleep_minutes` | Total sleep time | Sleep 7 hours (420 min) |
| `resting_heart_rate` | Resting heart rate | Keep RHR under 60 BPM |

## Viewing Metrics

### Daily Summary

On the Fitbit page, view today's metrics:

- Current values
- Progress toward goals
- Last sync time

### Historical Data

Sync historical data (up to 30 days) to backfill metrics:

```bash
curl -X POST http://localhost:8080/api/fitbit/sync?days=30 \
  -H "X-Profile-Id: 1"
```

## Sync Schedule

By default, Fitbit data syncs automatically every hour for all connected profiles.

This ensures your tasks auto-complete throughout the day as you reach goals.

## Disconnecting Fitbit

To disconnect your Fitbit account:

1. Go to **Settings** → **Fitbit Integration**
2. Click **"Disconnect Fitbit"**
3. Confirm the action

**Warning:** Disconnecting will:
- Revoke Streaklet's access to your Fitbit data
- Disable auto-check for all tasks (they'll remain as regular tasks)
- Preserve historical metric data (not deleted)

## Privacy & Security

- **Token Encryption**: Fitbit access tokens are encrypted at rest using AES-256
- **Read-Only Access**: Streaklet only requests read permissions
- **Local Storage**: All data is stored in your local SQLite database
- **No Sharing**: Data is never sent to external servers (except Fitbit API)

## Troubleshooting

### "Fitbit connection not found"

Your Fitbit connection may have expired. Reconnect:
1. Go to Settings
2. Click "Connect Fitbit" again

### Tasks not auto-completing

1. Verify Fitbit is connected: Check Settings page
2. Force a manual sync: Click "Sync Now"
3. Check task configuration: Ensure metric type and goal are correct
4. Check Fitbit data: Verify metrics exist in your Fitbit app

### Sync errors

Check Docker logs for detailed error messages:
```bash
docker logs streaklet
```

Common issues:
- Invalid credentials (check `FITBIT_CLIENT_ID` and `FITBIT_CLIENT_SECRET`)
- Expired refresh token (reconnect Fitbit)
- Rate limiting (Fitbit API has limits; sync will retry)

## API Reference

See the [Fitbit API documentation](../api/endpoints.md#fitbit-integration) for complete endpoint details.
