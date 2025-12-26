# Docker Compose Deployment

Deploy Streaklet using Docker Compose for easy management and configuration.

## Quick Start

### 1. Create docker-compose.yml

```yaml
services:
  streaklet:
    image: ghcr.io/ptmetcalf/streaklet:latest
    container_name: streaklet
    restart: unless-stopped
    ports:
      - "8080:8080"
    volumes:
      - ./data:/data
    environment:
      - APP_TIMEZONE=America/Chicago
      - DB_PATH=/data/app.db
      # Optional: Fitbit integration
      # - FITBIT_CLIENT_ID=your_client_id
      # - FITBIT_CLIENT_SECRET=your_client_secret
      # - APP_SECRET_KEY=your_random_32_char_secret
```

### 2. Prepare Data Directory

The Docker image runs as non-root user (uid 1000) for security:

```bash
mkdir -p data
chown -R 1000:1000 data
```

### 3. Start the Container

```bash
docker compose up -d
```

### 4. Access the Application

Open your browser to: `http://localhost:8080`

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `APP_TIMEZONE` | No | `America/Chicago` | IANA timezone for daily tracking |
| `DB_PATH` | No | `/data/app.db` | SQLite database file path |
| `PORT` | No | `8080` | Application port |
| `FITBIT_CLIENT_ID` | No | - | Fitbit OAuth client ID |
| `FITBIT_CLIENT_SECRET` | No | - | Fitbit OAuth client secret |
| `APP_SECRET_KEY` | No* | - | Secret key for token encryption |

\* Required if using Fitbit integration

### Timezone Configuration

Set your local timezone for accurate daily tracking:

```yaml
environment:
  - APP_TIMEZONE=America/New_York
```

Common timezones:
- `America/New_York` - Eastern Time
- `America/Chicago` - Central Time
- `America/Denver` - Mountain Time
- `America/Los_Angeles` - Pacific Time
- `Europe/London` - UK
- `Europe/Paris` - Central European Time
- `Asia/Tokyo` - Japan

[Full list of IANA timezones](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)

### Fitbit Integration

To enable Fitbit integration, add all three environment variables:

```yaml
environment:
  - FITBIT_CLIENT_ID=ABC123
  - FITBIT_CLIENT_SECRET=xyz789secretkey
  - APP_SECRET_KEY=your_secure_random_32_character_string
```

**Important:** Keep `APP_SECRET_KEY` consistent. Changing it will invalidate all encrypted Fitbit tokens.

Generate a secure key:
```bash
openssl rand -hex 32
```

## Storage

### Volume Mounts

Streaklet stores all data in `/data` inside the container. Mount this directory to persist data:

```yaml
volumes:
  - ./data:/data           # Host directory
  # Or use a named volume:
  # - streaklet-data:/data
```

### Named Volumes

For named volumes, define at the bottom of docker-compose.yml:

```yaml
services:
  streaklet:
    # ... configuration ...
    volumes:
      - streaklet-data:/data

volumes:
  streaklet-data:
```

List volumes:
```bash
docker volume ls
```

Inspect volume location:
```bash
docker volume inspect streaklet-data
```

### Permissions

The container runs as `appuser` (uid 1000, gid 1000). Ensure the data directory is writable:

```bash
# If using host directory
chown -R 1000:1000 ./data

# Verify permissions
ls -la ./data
```

## Networking

### Port Mapping

Change the host port:

```yaml
ports:
  - "3000:8080"  # Access at http://localhost:3000
```

### Reverse Proxy

For production use with reverse proxy (nginx, Traefik, Caddy):

```yaml
services:
  streaklet:
    # ... other config ...
    expose:
      - "8080"  # Don't publish ports directly
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.streaklet.rule=Host(`streaklet.example.com`)"
```

See [Homelab Integration](homelab.md) for reverse proxy examples.

## Updates

### Pulling Updates

```bash
docker compose pull
docker compose up -d
```

This pulls the latest image and recreates the container.

### Viewing Logs

```bash
# Follow logs in real-time
docker compose logs -f

# View last 100 lines
docker compose logs --tail=100

# View logs for specific time range
docker compose logs --since=1h
```

### Restarting

```bash
# Restart the service
docker compose restart

# Stop and start (recreates containers)
docker compose down
docker compose up -d
```

## Backup

### Database Backup

**Recommended:** Use the built-in backup API (see [Backup & Restore](../features/backup.md))

**Alternative:** Copy the SQLite database directly:

```bash
# Stop the container first
docker compose stop

# Copy database
cp ./data/app.db ./backups/app-$(date +%Y-%m-%d).db

# Start the container
docker compose start
```

### Automated Backups

Add a backup service to docker-compose.yml:

```yaml
services:
  streaklet:
    # ... streaklet config ...

  backup:
    image: alpine:latest
    container_name: streaklet-backup
    volumes:
      - ./data:/data:ro  # Read-only
      - ./backups:/backups
    command: |
      sh -c "
      while true; do
        cp /data/app.db /backups/app-\$(date +%Y-%m-%d).db
        sleep 86400  # Daily
      done
      "
```

## Health Checks

Docker Compose health check:

```yaml
services:
  streaklet:
    # ... other config ...
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

Check health status:
```bash
docker compose ps
```

## Troubleshooting

### Container won't start

Check logs:
```bash
docker compose logs
```

Common issues:
- **Permission denied**: Run `chown -R 1000:1000 ./data`
- **Port already in use**: Change port mapping or stop conflicting service
- **Invalid environment variable**: Check `.env` file syntax

### Cannot write to database

Ensure data directory is writable by uid 1000:
```bash
sudo chown -R 1000:1000 ./data
```

### Fitbit connection fails

Verify environment variables are set:
```bash
docker compose exec streaklet env | grep FITBIT
```

Check callback URL in Fitbit app settings matches:
```
http://your-domain:8080/api/fitbit/callback
```

### Container keeps restarting

View restart count:
```bash
docker compose ps
```

Check logs for error messages:
```bash
docker compose logs --tail=50
```

Common causes:
- Database corruption (restore from backup)
- Filesystem issues (check disk space: `df -h`)
- Invalid configuration

## Advanced Configuration

### Resource Limits

Limit CPU and memory usage:

```yaml
services:
  streaklet:
    # ... other config ...
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          memory: 256M
```

### Custom Network

Create isolated network:

```yaml
networks:
  streaklet-net:
    driver: bridge

services:
  streaklet:
    networks:
      - streaklet-net
```

### Read-Only Root Filesystem

For extra security:

```yaml
services:
  streaklet:
    # ... other config ...
    read_only: true
    tmpfs:
      - /tmp
```

## Complete Example

Full-featured docker-compose.yml:

```yaml
version: '3.8'

services:
  streaklet:
    image: ghcr.io/ptmetcalf/streaklet:latest
    container_name: streaklet
    restart: unless-stopped
    ports:
      - "8080:8080"
    volumes:
      - streaklet-data:/data
    environment:
      - APP_TIMEZONE=America/Chicago
      - DB_PATH=/data/app.db
      - FITBIT_CLIENT_ID=${FITBIT_CLIENT_ID}
      - FITBIT_CLIENT_SECRET=${FITBIT_CLIENT_SECRET}
      - APP_SECRET_KEY=${APP_SECRET_KEY}
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
    labels:
      - "com.example.description=Streaklet habit tracker"
      - "com.example.version=1.0"

volumes:
  streaklet-data:
    driver: local

networks:
  default:
    driver: bridge
```

With `.env` file:
```bash
FITBIT_CLIENT_ID=your_client_id
FITBIT_CLIENT_SECRET=your_secret
APP_SECRET_KEY=your_secure_random_key_32_chars_min
```

## Next Steps

- [Homelab Integration](homelab.md) - Integrate with reverse proxies and home servers
- [Configuration Guide](../getting-started/configuration.md) - Detailed configuration options
- [Backup & Restore](../features/backup.md) - Data backup strategies
