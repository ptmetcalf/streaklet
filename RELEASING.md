# Release Process

This project has automated releases via GitHub Actions.

## How to Create a Release

1. **Decide on version number** (follow [Semantic Versioning](https://semver.org/)):
   - `v1.0.0` - Major version (breaking changes)
   - `v0.1.0` - Minor version (new features, backward compatible)
   - `v0.0.1` - Patch version (bug fixes)

2. **Tag and push:**
   ```bash
   # Create annotated tag
   git tag -a v1.0.0 -m "Release v1.0.0: Description of changes"

   # Push tag to GitHub
   git push origin v1.0.0
   ```

3. **Automated workflow runs:**
   - ✅ Runs all tests
   - ✅ Builds Docker images (amd64, arm64)
   - ✅ Pushes to GitHub Container Registry
   - ✅ Creates GitHub Release with auto-generated notes

## What Gets Created

The release will include:
- **Changelog:** Auto-generated from git commits since last tag
- **Docker image info:** Pull command and platform support
- **Release notes:** Generated from PR titles and commit messages
- **Tagged images:**
  - `ghcr.io/yourusername/streaklet:1.0.0`
  - `ghcr.io/yourusername/streaklet:1.0`
  - `ghcr.io/yourusername/streaklet:1`
  - `ghcr.io/yourusername/streaklet:latest` (if on main branch)

## Example Release Notes

When you push `v1.2.3`, the action automatically creates a release like:

```markdown
## What's Changed
- Fix timezone handling in Fitbit page (abc1234)
- Add hardened Docker build with multi-stage setup (def5678)
- Update dependencies to latest versions (ghi9012)

## Docker Image

\`\`\`bash
docker pull ghcr.io/yourusername/streaklet:1.2.3
\`\`\`

**Multi-platform support:** linux/amd64, linux/arm64

**Security:** This image uses a hardened multi-stage build running as non-root user
```

## Quick Release Commands

```bash
# Patch release (bug fixes)
git tag -a v1.0.1 -m "Release v1.0.1: Fix timezone bug"
git push origin v1.0.1

# Minor release (new features)
git tag -a v1.1.0 -m "Release v1.1.0: Add Fitbit integration"
git push origin v1.1.0

# Major release (breaking changes)
git tag -a v2.0.0 -m "Release v2.0.0: New API, breaking changes"
git push origin v2.0.0
```

## Viewing Releases

- **GitHub UI:** https://github.com/yourusername/streaklet/releases
- **Docker Images:** https://github.com/yourusername/streaklet/pkgs/container/streaklet

## Tips

- **Write good commit messages** - They become your release notes!
- **Use conventional commits** for better changelogs:
  - `feat: Add new feature`
  - `fix: Fix bug in authentication`
  - `docs: Update README`
  - `chore: Update dependencies`

- **Test before tagging:**
  ```bash
  # Make sure CI is green on main/develop first
  git push origin main
  # Wait for CI to pass, then tag
  ```

## Rollback

If you need to delete a release/tag:

```bash
# Delete tag locally
git tag -d v1.0.0

# Delete tag on GitHub
git push origin :refs/tags/v1.0.0

# Manually delete the GitHub Release in the web UI
```
