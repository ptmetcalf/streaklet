# Configuration

Streaklet is configured via environment variables.

## Environment Variables

### Core Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_TIMEZONE` | `America/Chicago` | Timezone for daily tracking (IANA format) |
| `DB_PATH` | `/data/app.db` | Path to SQLite database file |
| `PORT` | `8080` | HTTP server port |

### Fitbit Integration

| Variable | Required | Description |
|----------|----------|-------------|
| `FITBIT_CLIENT_ID` | Yes* | Your Fitbit OAuth client ID |
| `FITBIT_CLIENT_SECRET` | Yes* | Your Fitbit OAuth client secret |
| `FITBIT_CALLBACK_URL` | Yes* | OAuth callback URL (e.g., `http://localhost:8080/api/fitbit/callback`) |
| `APP_SECRET_KEY` | Yes* | 32-byte secret key for token encryption |
| `FITBIT_SYNC_INTERVAL_HOURS` | `1` | How often to sync Fitbit data (hours) |

\* Required only if using Fitbit integration

## Configuration Methods

### Docker Compose

Edit `.env` file:

```bash
APP_TIMEZONE=America/New_York
DB_PATH=/data/app.db
PORT=8080

# Fitbit (optional)
FITBIT_CLIENT_ID=ABC123
FITBIT_CLIENT_SECRET=def456xyz
FITBIT_CALLBACK_URL=http://localhost:8080/api/fitbit/callback
APP_SECRET_KEY=your_32_byte_secret_key_here_1234
FITBIT_SYNC_INTERVAL_HOURS=2
```

Then restart:
```bash
docker compose restart
```

### Docker CLI

Pass via `-e` flags:

```bash
docker run -d \
  -e APP_TIMEZONE=America/New_York \
  -e DB_PATH=/data/app.db \
  -e FITBIT_CLIENT_ID=ABC123 \
  -p 8080:8080 \
  ghcr.io/ptmetcalf/streaklet:latest
```

## Timezone Configuration

Use IANA timezone names: [Full List](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)

**Common timezones:**
- `America/New_York` - Eastern Time
- `America/Chicago` - Central Time
- `America/Denver` - Mountain Time
- `America/Los_Angeles` - Pacific Time
- `America/Phoenix` - Arizona (no DST)
- `Europe/London` - UK
- `Europe/Paris` - Central European Time
- `Asia/Tokyo` - Japan Standard Time
- `Australia/Sydney` - Australian Eastern Time

## Fitbit Setup

See the [Fitbit Integration Guide](../features/fitbit.md) for detailed setup instructions.

### Generating APP_SECRET_KEY

```bash
# Generate a secure 32-byte key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Volume Mounts

The `/data` directory should be mounted to persist:
- SQLite database (`app.db`)
- Fitbit tokens (encrypted)

```bash
docker run -v ./data:/data [...]
```

## Port Configuration

Change the external port if 8080 is in use:

```bash
# Run on port 3000 instead
docker run -p 3000:8080 [...]
```

The internal port (8080) stays the same.

## Security Considerations

- **APP_SECRET_KEY**: Keep this secret! Used to encrypt Fitbit tokens
- **Network**: Streaklet has no authentication - deploy on trusted networks only
- **Data Directory**: Set proper permissions (`chown 1000:1000 ./data`)
- **Reverse Proxy**: Use HTTPS if exposing to internet

## Advanced Configuration

### Custom Database Path

```bash
DB_PATH=/custom/path/streaklet.db
```

Ensure the directory is writable by uid 1000.

### Sync Interval

Control how often Fitbit data syncs:

```bash
FITBIT_SYNC_INTERVAL_HOURS=3  # Sync every 3 hours
```

Lower values mean more frequent syncs but more API calls.

## Troubleshooting

### Wrong Timezone

Check your timezone is valid:

```bash
docker exec streaklet python -c "from zoneinfo import ZoneInfo; print(ZoneInfo('America/Chicago'))"
```

### Fitbit Not Syncing

1. Check `FITBIT_SYNC_INTERVAL_HOURS` is set
2. View logs: `docker logs streaklet`
3. Manually sync from Settings page

### Permission Errors

```bash
sudo chown -R 1000:1000 ./data
docker restart streaklet
```
