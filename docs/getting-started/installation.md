# Installation

Streaklet is distributed as a Docker container for easy deployment.

## Prerequisites

- Docker and Docker Compose installed
- (Optional) Fitbit Developer Application for Fitbit integration

## Installation Methods

=== "Docker Compose (Recommended)"

    ### 1. Clone the Repository

    ```bash
    git clone https://github.com/ptmetcalf/streaklet.git
    cd streaklet
    ```

    ### 2. Create Environment File

    ```bash
    cp .env.example .env
    ```

    Edit `.env` and configure:

    ```bash
    APP_TIMEZONE=America/Chicago
    DB_PATH=/data/app.db
    PORT=8080

    # For Fitbit integration (optional)
    FITBIT_CLIENT_ID=your_client_id
    FITBIT_CLIENT_SECRET=your_client_secret
    FITBIT_CALLBACK_URL=http://localhost:8080/api/fitbit/callback
    APP_SECRET_KEY=your_32_byte_secret_key
    ```

    ### 3. Start the Application

    ```bash
    docker compose up -d
    ```

    Access at: `http://localhost:8080`

=== "GitHub Container Registry"

    ### Pull Pre-Built Image

    ```bash
    docker pull ghcr.io/ptmetcalf/streaklet:latest
    ```

    ### Run Container

    ```bash
    docker run -d \
      --name streaklet \
      -p 8080:8080 \
      -v ./data:/data \
      -e APP_TIMEZONE=America/Chicago \
      -e DB_PATH=/data/app.db \
      ghcr.io/ptmetcalf/streaklet:latest
    ```

=== "Docker CLI"

    ### Build from Source

    ```bash
    git clone https://github.com/ptmetcalf/streaklet.git
    cd streaklet
    docker build -t streaklet .
    ```

    ### Run Container

    ```bash
    docker run -d \
      --name streaklet \
      -p 8080:8080 \
      -v ./data:/data \
      -e APP_TIMEZONE=America/Chicago \
      -e DB_PATH=/data/app.db \
      streaklet
    ```

## Verify Installation

Check that the container is healthy:

```bash
docker ps
curl http://localhost:8080/health
```

Expected response:
```json
{"status": "healthy"}
```

## First Launch

1. Navigate to `http://localhost:8080`
2. You'll be redirected to the Profiles page
3. A default profile is automatically created
4. Start adding tasks and tracking your streaks!

## Updating

### Docker Compose

```bash
docker compose pull
docker compose up -d
```

### Docker CLI

```bash
docker pull ghcr.io/ptmetcalf/streaklet:latest
docker stop streaklet
docker rm streaklet
docker run -d --name streaklet [... same options as above ...]
```

## Troubleshooting

### Permission Errors

If you see "readonly database" errors, fix data directory permissions:

```bash
chown -R 1000:1000 ./data
docker restart streaklet
```

The hardened Docker image runs as a non-root user (uid 1000) for security.

### Port Already in Use

Change the port mapping in docker-compose.yml or use a different port:

```bash
docker run -p 8081:8080 [...]
```

### Database Migrations Failed

Manually run migrations:

```bash
docker exec streaklet alembic upgrade head
```

## Next Steps

- [Configuration Guide](configuration.md) - Environment variables and settings
- [Quick Start Tutorial](quick-start.md) - Learn the basics
- [Fitbit Setup](../features/fitbit.md) - Connect your Fitbit device
