# Streaklet

[![CI](https://github.com/ptmetcalf/streaklet/actions/workflows/ci.yml/badge.svg)](https://github.com/ptmetcalf/streaklet/actions/workflows/ci.yml)
[![Docker](https://github.com/ptmetcalf/streaklet/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/ptmetcalf/streaklet/actions/workflows/docker-publish.yml)
[![codecov](https://codecov.io/gh/ptmetcalf/streaklet/branch/main/graph/badge.svg)](https://codecov.io/gh/ptmetcalf/streaklet)
[![Documentation](https://img.shields.io/badge/docs-mkdocs-blue)](https://ptmetcalf.github.io/streaklet)

A self-hosted, Dockerized daily habit streak tracker with multi-user profile support.

## Features

- **Three Task Types** - Daily habits, one-off todos, scheduled recurring tasks
- **Multi-User Profiles** - Completely isolated data per user
- **Fitbit Integration** - Auto-complete tasks based on fitness metrics
- **Progressive Web App** - Install on mobile/desktop
- **Offline Support** - Service worker caching
- **Automatic Streaks** - Track consecutive completion days
- **Timezone-Aware** - Accurate daily tracking worldwide
- **Backup & Restore** - Export/import profile data

## Quick Start

```bash
docker pull ghcr.io/ptmetcalf/streaklet:latest
docker run -d -p 8080:8080 -v ./data:/data ghcr.io/ptmetcalf/streaklet:latest
```

Access at: `http://localhost:8080`

## Documentation

📚 **[Full Documentation](https://ptmetcalf.github.io/streaklet)**

- [Installation Guide](https://ptmetcalf.github.io/streaklet/getting-started/installation/)
- [Fitbit Setup](https://ptmetcalf.github.io/streaklet/features/fitbit/)
- [API Reference](https://ptmetcalf.github.io/streaklet/api/endpoints/)
- [Contributing](https://ptmetcalf.github.io/streaklet/development/contributing/)

## Contributing

We use [Conventional Commits](https://www.conventionalcommits.org/) for automated releases.

```bash
feat: add dark mode        # Minor version bump
fix: resolve timezone bug  # Patch version bump
docs: update README        # No release
```

See [Contributing Guide](https://ptmetcalf.github.io/streaklet/development/contributing/) for details.

## Tech Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy 2.0
- **Database**: SQLite
- **Frontend**: Jinja2, Alpine.js, HTMX
- **Deployment**: Docker, Docker Compose

## License

MIT - See [LICENSE](LICENSE)
