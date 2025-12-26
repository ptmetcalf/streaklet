# User Profiles

Streaklet supports multiple user profiles, allowing families or households to track habits independently while sharing the same installation.

## Overview

Each profile has:

- **Completely isolated data** - tasks, completions, streaks, and history
- **Custom color** - for visual identification in the UI
- **Unique name** - to distinguish between users

## Creating Profiles

### Via Web Interface

1. Navigate to the **Profiles** page
2. Click **"Add Profile"**
3. Enter a name (e.g., "Mom", "Dad", "Alex")
4. Choose a color for visual identification
5. Click **Save**

### Via API

```bash
curl -X POST http://localhost:8080/api/profiles \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Alex",
    "color": "#3b82f6"
  }'
```

**Response:**
```json
{
  "id": 2,
  "name": "Alex",
  "color": "#3b82f6"
}
```

## Default Profile

On first run, Streaklet automatically creates a default profile (ID: 1) named "Default Profile".

New profiles are automatically seeded with 5 default tasks:
- Follow a diet
- 30 min workout
- Read 10 pages
- 20 min hobby time
- Drink 8 glasses water

You can edit or delete these tasks as needed.

## Switching Profiles

The active profile is stored in browser localStorage and persists across sessions.

**To switch profiles:**
1. Click the profile selector (typically in the header)
2. Select the desired profile
3. The page reloads with that profile's data

## Data Isolation

Profile isolation is enforced at multiple levels:

- **Database level** - All tables include a `user_id` foreign key
- **API level** - All requests include an `X-Profile-Id` header
- **Service level** - All queries filter by profile ID

This ensures complete data separation between profiles.

## Profile Management

### Editing Profiles

Update a profile's name or color:

```bash
curl -X PUT http://localhost:8080/api/profiles/2 \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Alexander",
    "color": "#8b5cf6"
  }'
```

### Deleting Profiles

**Warning:** Deleting a profile permanently removes:
- All tasks
- All completion history
- All daily status records
- Fitbit connection (if any)

You cannot delete the last remaining profile.

```bash
curl -X DELETE http://localhost:8080/api/profiles/2
```

### Backup Before Deletion

Always [backup profile data](backup.md) before deletion:

```bash
curl http://localhost:8080/api/backup/profile/2 > profile-backup.json
```

## Multi-Device Usage

Since profile selection is stored in browser localStorage:

- Each device/browser can be set to a different profile
- Perfect for shared family computers (each browser = different user)
- Mobile and desktop can track different profiles

## API Reference

See the [Profile Management API documentation](../api/endpoints.md#profile-management) for complete endpoint details.
