# Contributing

Thank you for contributing to Streaklet! This guide will help you get started.

## Commit Message Format

This project uses [Conventional Commits](https://www.conventionalcommits.org/) for automated releases.

### Format

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types

| Type | Description | Version Bump |
|------|-------------|--------------|
| `feat` | New feature | Minor (1.0.0 → 1.1.0) |
| `fix` | Bug fix | Patch (1.0.0 → 1.0.1) |
| `feat!` or `BREAKING CHANGE:` | Breaking change | Major (1.0.0 → 2.0.0) |
| `docs` | Documentation only | None |
| `chore` | Maintenance tasks | None |
| `refactor` | Code restructuring | None |
| `test` | Test additions/changes | None |
| `ci` | CI/CD changes | None |
| `perf` | Performance improvement | Patch |

### Examples

```bash
# Feature (minor bump)
feat: add dark mode toggle to settings

# Bug fix (patch bump)
fix: resolve timezone display issue in Fitbit page

# Breaking change (major bump)
feat!: redesign API authentication

BREAKING CHANGE: API now requires JWT tokens instead of API keys

# Documentation (no release)
docs: update installation instructions

# Maintenance (no release)
chore: update dependencies
```

## Development Setup

### Prerequisites

- Python 3.12+
- Docker and Docker Compose
- Git

### Local Development

1. **Clone and setup:**

```bash
git clone https://github.com/ptmetcalf/streaklet.git
cd streaklet

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

2. **Run locally:**

```bash
# Start development server
./dev.sh run

# Or with uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

3. **Run tests:**

```bash
# All tests
./dev.sh test

# With coverage
./dev.sh test-cov

# Single test file
python -m pytest tests/test_profiles.py -v
```

4. **Lint code:**

```bash
# Activate venv first
source .venv/bin/activate

# Check for errors
ruff check app/ tests/

# Auto-fix
ruff check app/ tests/ --fix
```

### Docker Development

```bash
# Build and run
docker compose up --build

# Run tests in Docker
docker build -t streaklet:test .
docker run --rm --entrypoint "" --user appuser streaklet:test \
  sh -c "PYTHONPATH=. python -m pytest tests/ -v"
```

## Pull Request Process

1. **Create a feature branch:**

```bash
git checkout -b feat/your-feature-name
```

2. **Make changes with conventional commits:**

```bash
git add .
git commit -m "feat: add user export functionality"
git push origin feat/your-feature-name
```

3. **Open Pull Request:**
   - Target the `main` or `develop` branch
   - Use conventional commit format in PR title
   - Describe changes clearly
   - Link related issues

4. **CI must pass:**
   - Linting
   - Unit tests
   - Docker build
   - Integration tests

5. **Review and merge:**
   - Maintainer reviews
   - Merge when approved and CI passes

## Release Process

Releases are automated via release-please:

1. Merge PR to `main` with conventional commits
2. release-please creates a Release PR automatically
3. Maintainer reviews and merges Release PR
4. GitHub Release created
5. Docker images published

See [Releases Documentation](releases.md) for details.

## Code Style

- Follow PEP 8
- Use type hints
- Write docstrings for public functions
- Keep functions focused and small
- Write tests for new features

## Testing Guidelines

- Write tests for all new features
- Maintain or improve code coverage
- Test edge cases
- Use pytest fixtures appropriately

### Test Structure

```python
def test_feature_description(test_db, sample_profiles):
    """Test that feature does X when Y happens."""
    # Arrange
    setup_data(test_db)

    # Act
    result = function_under_test()

    # Assert
    assert result == expected
```

## Documentation

- Update docs/ for user-facing changes
- Update CLAUDE.md for architecture changes
- Add docstrings for code documentation
- Include examples where helpful

## Security

- Run as non-root user (uid 1000)
- No hardcoded secrets
- Validate user input
- Use parameterized SQL queries
- Follow OWASP security practices

## Questions?

- Open an issue for bugs or feature requests
- Discussion tab for questions
- Check existing issues first

## Code of Conduct

Be respectful and constructive in all interactions.
