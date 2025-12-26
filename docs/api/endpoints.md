# API Endpoints

Streaklet provides a REST API for programmatic access.

## Profile Context

All endpoints (except `/api/profiles`) accept an optional `X-Profile-Id` header to specify which profile's data to access.

If not provided, defaults to profile ID 1.

```bash
# Default (profile 1)
curl http://localhost:8080/api/tasks

# Specific profile
curl -H "X-Profile-Id: 2" http://localhost:8080/api/tasks
```

## Profile Management

### List Profiles

```http
GET /api/profiles
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "John",
    "color": "#3b82f6",
    "created_at": "2025-01-01T00:00:00Z"
  }
]
```

### Get Profile

```http
GET /api/profiles/{id}
```

### Create Profile

```http
POST /api/profiles
Content-Type: application/json

{
  "name": "Jane",
  "color": "#ef4444"
}
```

### Update Profile

```http
PUT /api/profiles/{id}
Content-Type: application/json

{
  "name": "Jane Doe",
  "color": "#10b981"
}
```

### Delete Profile

```http
DELETE /api/profiles/{id}
```

## Tasks

### List Tasks

```http
GET /api/tasks
X-Profile-Id: 1
```

**Response:**
```json
[
  {
    "id": 1,
    "title": "Exercise 30 minutes",
    "is_required": true,
    "is_active": true,
    "sort_order": 1,
    "fitbit_metric_type": "active_minutes",
    "fitbit_goal_value": 30.0,
    "fitbit_goal_operator": "gte",
    "fitbit_auto_check": true
  }
]
```

### Create Task

```http
POST /api/tasks
X-Profile-Id: 1
Content-Type: application/json

{
  "title": "Read 10 pages",
  "is_required": true,
  "is_active": true,
  "sort_order": 1
}
```

### Update Task

```http
PUT /api/tasks/{id}
X-Profile-Id: 1
Content-Type: application/json

{
  "title": "Read 20 pages",
  "is_required": false
}
```

### Delete Task

```http
DELETE /api/tasks/{id}
X-Profile-Id: 1
```

## Daily Checklist

### Get Today's Checklist

```http
GET /api/days/today
X-Profile-Id: 1
```

**Response:**
```json
{
  "date": "2025-01-15",
  "tasks": [
    {
      "id": 1,
      "title": "Exercise 30 minutes",
      "checked": true,
      "checked_at": "2025-01-15T10:30:00Z",
      "is_required": true,
      "fitbit_current_value": 35.0,
      "fitbit_goal_met": true
    }
  ],
  "all_required_complete": false,
  "completed_at": null,
  "streak": {
    "current_streak": 5,
    "today_complete": false,
    "last_completed_date": "2025-01-14"
  }
}
```

### Toggle Task Check

```http
PUT /api/days/{date}/checks/{task_id}
X-Profile-Id: 1
Content-Type: application/json

{
  "checked": true
}
```

## Streaks

### Get Streak Info

```http
GET /api/streak
X-Profile-Id: 1
```

**Response:**
```json
{
  "current_streak": 7,
  "today_complete": true,
  "last_completed_date": "2025-01-15"
}
```

## History

### Get Calendar Month

```http
GET /api/history/{year}/{month}
X-Profile-Id: 1
```

**Example:**
```http
GET /api/history/2025/1
```

**Response:**
```json
{
  "calendar_data": {
    "year": 2025,
    "month": 1,
    "days_in_month": 31,
    "first_day_weekday": 2,
    "days": {
      "2025-01-15": {
        "date": "2025-01-15",
        "completed": true,
        "completed_at": "2025-01-15T22:00:00Z",
        "completion_rate": 100
      }
    }
  },
  "streak": {
    "current_streak": 7,
    "today_complete": true,
    "last_completed_date": "2025-01-15"
  }
}
```

## Backup & Import

### Export Profile

```http
GET /api/profiles/{id}/export
```

Downloads JSON file with profile data.

### Import Profile

```http
POST /api/profiles/{id}/import
Content-Type: multipart/form-data

file: backup.json
mode: replace  # or "merge"
```

### Export All Profiles

```http
GET /api/profiles/export/all
```

### Import All Profiles

```http
POST /api/profiles/import/all
Content-Type: multipart/form-data

file: all_profiles.json
mode: replace  # or "merge"
```

## Fitbit Integration

### Check Connection

```http
GET /api/fitbit/connection
X-Profile-Id: 1
```

### Get Auth URL

```http
GET /api/fitbit/auth
X-Profile-Id: 1
```

### Disconnect

```http
POST /api/fitbit/disconnect
X-Profile-Id: 1
```

### Manual Sync

```http
POST /api/fitbit/sync
X-Profile-Id: 1
```

### Get Daily Summary

```http
GET /api/fitbit/daily-summary?date=2025-01-15
X-Profile-Id: 1
```

## Health Check

```http
GET /health
```

**Response:**
```json
{"status": "healthy"}
```

## Rate Limiting

No rate limiting is currently implemented. Use responsibly.

## Error Responses

Errors follow this format:

```json
{
  "detail": "Error message description"
}
```

Common status codes:
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `404` - Not Found
- `500` - Internal Server Error
