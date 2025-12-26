# API Overview

Streaklet provides a REST API for programmatic access to all features.

## Base URL

```
http://localhost:8080/api
```

## Authentication

Streaklet does not require authentication. It's designed for use on trusted networks.

**Security Note:** Do not expose Streaklet directly to the internet without additional authentication layers.

## Profile Context

Most endpoints require a profile context via the `X-Profile-Id` header:

```bash
curl -H "X-Profile-Id: 1" http://localhost:8080/api/tasks
```

If omitted, defaults to profile ID 1.

## Response Format

All responses are JSON.

**Success Response:**
```json
{
  "id": 1,
  "name": "value"
}
```

**Error Response:**
```json
{
  "detail": "Error message"
}
```

## Endpoint Categories

- **[Profile Management](endpoints.md#profile-management)** - Create, list, update profiles
- **[Tasks](endpoints.md#tasks)** - Manage tasks for profiles
- **[Daily Checklist](endpoints.md#daily-checklist)** - Get today's tasks and toggle completion
- **[Streaks](endpoints.md#streaks)** - Get streak information
- **[History](endpoints.md#history)** - Access calendar and completion history
- **[Backup & Import](endpoints.md#backup-import)** - Export and import profile data
- **[Fitbit](endpoints.md#fitbit-integration)** - Fitbit OAuth and sync

## Complete API Reference

See [Endpoints Documentation](endpoints.md) for full API reference with examples.

## Client Libraries

Currently no official client libraries exist. The API is simple REST - use any HTTP client.

**Example with Python:**
```python
import requests

response = requests.get(
    "http://localhost:8080/api/tasks",
    headers={"X-Profile-Id": "1"}
)
tasks = response.json()
```

**Example with JavaScript:**
```javascript
const response = await fetch('http://localhost:8080/api/tasks', {
  headers: { 'X-Profile-Id': '1' }
});
const tasks = await response.json();
```

## Rate Limiting

No rate limiting is currently implemented.

## Versioning

The API is not versioned. Changes will be backwards compatible where possible, with breaking changes noted in release notes.
