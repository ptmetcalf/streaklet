# Release Process

Streaklet uses automated releases via [release-please](https://github.com/googleapis/release-please).

## How It Works

1. **Commit with conventional format** to `main` branch
2. **release-please creates a Release PR** with:
   - Auto-calculated version bump
   - Generated CHANGELOG.md
3. **Merge the Release PR**
4. **GitHub Release created automatically**
5. **Docker images built and published**

## Version Bumping

| Commit Type | Version Change |
|-------------|----------------|
| `feat:` | 1.0.0 → **1.1.0** (minor) |
| `fix:` | 1.0.0 → **1.0.1** (patch) |
| `feat!:` or `BREAKING CHANGE:` | 1.0.0 → **2.0.0** (major) |
| `docs:`, `chore:`, etc. | No release |

## Typical Workflow

### 1. Make Changes

```bash
git checkout -b feat/new-feature
# Make changes
git commit -m "feat: add export functionality"
git push
```

### 2. Create PR

- Use conventional commit format in PR title
- Get review and approval
- Merge to `main`

### 3. Wait for Release PR

After merge, release-please creates a PR like:

**Title:** `chore(main): release 1.1.0`

**Contents:**
```markdown
## 1.1.0 (2025-01-15)

### Features

* add export functionality ([abc1234](link))
* implement user profiles ([def5678](link))

### Bug Fixes

* resolve timezone issue ([ghi9012](link))
```

### 4. Merge Release PR

- Review the version number and changelog
- Merge the Release PR
- Release happens automatically!

### 5. Docker Images Published

Images are tagged and published:
- `ghcr.io/ptmetcalf/streaklet:1.1.0`
- `ghcr.io/ptmetcalf/streaklet:1.1`
- `ghcr.io/ptmetcalf/streaklet:1`
- `ghcr.io/ptmetcalf/streaklet:latest`

## Checking Release Status

- **Open PRs:** Look for `chore(main): release X.Y.Z`
- **Releases:** [GitHub Releases](https://github.com/ptmetcalf/streaklet/releases)
- **Docker Images:** [Container Registry](https://github.com/ptmetcalf/streaklet/pkgs/container/streaklet)
- **Workflows:** [GitHub Actions](https://github.com/ptmetcalf/streaklet/actions)

## Emergency Manual Release

If automated releases fail:

```bash
# Create tag manually
git tag -a v1.2.3 -m "Emergency release"
git push origin v1.2.3

# Manually create GitHub Release in UI
```

## Configuration Files

- `.release-please-manifest.json` - Current version
- `release-please-config.json` - Settings
- `.github/workflows/release-please.yml` - Workflow

## For Detailed Information

See [RELEASING.md](https://github.com/ptmetcalf/streaklet/blob/main/RELEASING.md) for comprehensive release documentation.
