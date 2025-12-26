# Release Process (Automated with release-please)

This project uses [release-please](https://github.com/googleapis/release-please) for automated releases.

## How It Works

1. **You commit using conventional commits** (explained below)
2. **release-please automatically creates a Release PR** with:
   - Auto-calculated version bump
   - Generated CHANGELOG.md
   - Updated version files
3. **You merge the Release PR**
4. **GitHub Release is created automatically**
5. **Docker images are built and published**

## Conventional Commits

Use this format for commit messages:

```bash
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types (determines version bump):

- **`feat:`** - New feature → **Minor version bump** (1.0.0 → 1.1.0)
- **`fix:`** - Bug fix → **Patch version bump** (1.0.0 → 1.0.1)
- **`feat!:`** or `BREAKING CHANGE:` - Breaking change → **Major version bump** (1.0.0 → 2.0.0)
- **`docs:`** - Documentation only (no version bump)
- **`chore:`** - Maintenance tasks (no version bump)
- **`refactor:`** - Code restructuring (no version bump)
- **`perf:`** - Performance improvement → Patch bump
- **`test:`** - Adding tests (no version bump)
- **`ci:`** - CI/CD changes (no version bump)

### Examples:

```bash
# Minor version bump (new feature)
git commit -m "feat: add dark mode toggle to settings"

# Patch version bump (bug fix)
git commit -m "fix: resolve timezone display issue in Fitbit page"

# Multiple changes
git commit -m "feat: add user profile export

Allows users to export their profile data as JSON.
Includes export button in settings page.

Closes #123"

# Breaking change (major version bump)
git commit -m "feat!: redesign API authentication

BREAKING CHANGE: API now requires JWT tokens instead of API keys.
All clients need to update authentication."
```

## Typical Workflow

### 1. Make Changes and Commit

```bash
git checkout -b feature/dark-mode
# Make your changes
git add .
git commit -m "feat: add dark mode toggle"
git push origin feature/dark-mode
```

### 2. Create PR to Main

```bash
# Create PR on GitHub
# Get it reviewed and approved
# Merge to main
```

### 3. Wait for Release PR

After merging to main, release-please will:
- Analyze commits since last release
- Create a "Release PR" (titled like "chore(main): release 1.1.0")
- Include generated CHANGELOG

**Example Release PR:**
```markdown
## 1.1.0 (2025-01-15)

### Features

* add dark mode toggle ([abc1234](link))
* implement user profile export ([def5678](link))

### Bug Fixes

* resolve timezone display issue ([ghi9012](link))
```

### 4. Review and Merge Release PR

Check the Release PR:
- ✅ Version number looks correct
- ✅ CHANGELOG is accurate
- ✅ All changes since last release are included

Merge it → Release happens automatically!

### 5. Docker Images Published

Once the release is created:
- Multi-platform Docker images built (amd64, arm64)
- Published to `ghcr.io/yourusername/streaklet:1.1.0`
- Also tagged as `latest`

## Version Bumping Rules

release-please uses semantic versioning:

| Commits Since Last Release | Version Bump |
|----------------------------|--------------|
| `feat: new feature` | 1.0.0 → **1.1.0** (minor) |
| `fix: bug fix` | 1.0.0 → **1.0.1** (patch) |
| `feat!: breaking change` | 1.0.0 → **2.0.0** (major) |
| `docs: update README` | No release |
| `chore: update deps` | No release |
| Multiple fixes | 1.0.0 → **1.0.1** (patch) |
| Mix of feat + fix | 1.0.0 → **1.1.0** (minor wins) |
| Breaking + features | 1.0.0 → **2.0.0** (major wins) |

## Manual Release (Emergency)

If you need to create a release manually:

```bash
# Create and push tag
git tag -a v1.2.3 -m "Emergency release: critical security fix"
git push origin v1.2.3

# Manually create GitHub Release
# Docker images will still auto-build
```

## Checking Release Status

- **Open PRs:** https://github.com/yourusername/streaklet/pulls
  - Look for PR titled "chore(main): release X.Y.Z"
- **Releases:** https://github.com/yourusername/streaklet/releases
- **Docker Images:** https://github.com/yourusername/streaklet/pkgs/container/streaklet

## Tips

### Good Commit Messages

✅ **Good:**
```bash
git commit -m "feat: add export button to settings page"
git commit -m "fix: timezone bug in Fitbit metrics display"
git commit -m "docs: update installation instructions"
```

❌ **Bad:**
```bash
git commit -m "update stuff"
git commit -m "fixes"
git commit -m "wip"
```

### Combining Multiple Changes

If you have multiple commits in a PR:
```bash
# Option 1: Multiple conventional commits (each appears in changelog)
git commit -m "feat: add export functionality"
git commit -m "test: add export tests"
git commit -m "docs: document export feature"

# Option 2: Squash merge PR with conventional title
# PR title: "feat: add profile export functionality"
```

### Skip Release

If you merge commits that don't warrant a release:
```bash
git commit -m "chore: update dependencies"  # Won't create release
git commit -m "docs: fix typo in README"    # Won't create release
```

## Configuration Files

- `.release-please-manifest.json` - Current version
- `release-please-config.json` - release-please settings
- `.github/workflows/release-please.yml` - Release workflow

## Troubleshooting

**Release PR not created?**
- Check commits use conventional format
- Ensure commits are on `main` branch
- Look for workflow run in Actions tab

**Wrong version bump?**
- Check commit types (feat vs fix vs chore)
- Remember: breaking changes need `!` or `BREAKING CHANGE:`

**Need to skip a release?**
- Close the Release PR without merging
- Next Release PR will include those changes

## Resources

- [Conventional Commits](https://www.conventionalcommits.org/)
- [release-please docs](https://github.com/googleapis/release-please)
- [Semantic Versioning](https://semver.org/)
