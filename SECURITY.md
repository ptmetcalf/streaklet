# Docker Security Hardening

## Overview

This document explains the security improvements in `Dockerfile.hardened` compared to the original `Dockerfile`.

## Security Improvements

### 1. **Multi-Stage Build** ✅
**Before:** Build tools (gcc, binutils, etc.) remained in final image
**After:** Build dependencies isolated in builder stage and discarded

**Impact:**
- Reduces attack surface by removing compilers and build tools
- Attacker cannot compile malicious code inside container
- 166MB smaller image (43% reduction: 388MB → 222MB)

### 2. **Non-Root User** ✅
**Before:** Application runs as `root` (uid 0)
**After:** Application runs as `appuser` (uid 1000)

**Impact:**
- If application is compromised, attacker has limited permissions
- Cannot modify system files or install packages
- Cannot access other containers or host system
- Industry best practice for production deployments

### 3. **Proper File Permissions** ✅
**Before:** All files owned by root
**After:** Application files owned by `appuser:appuser`

**Impact:**
- Non-root user can only access necessary files
- Database directory has proper ownership for writes
- Follows principle of least privilege

### 4. **Health Check** ✅
**Before:** No health check
**After:** Built-in health check using Python (no curl needed)

**Impact:**
- Container orchestrators can detect unhealthy containers
- No need to install curl (reduces attack surface)
- Automatic restart on failure

### 5. **Security Labels** ✅
**After:** Added metadata labels for tracking

**Impact:**
- Easier to identify hardened images in registries
- Helps with compliance and auditing

## Comparison

| Metric | Original | Hardened | Improvement |
|--------|----------|----------|-------------|
| **Image Size** | 388 MB | 222 MB | **43% smaller** |
| **Running User** | root (uid 0) | appuser (uid 1000) | **Non-root** ✅ |
| **Build Tools in Image** | Yes (gcc, binutils) | No | **Removed** ✅ |
| **Shell Available** | /bin/bash | /bin/sh | **Minimal** ✅ |
| **Health Check** | No | Yes | **Added** ✅ |
| **File Permissions** | root:root | appuser:appuser | **Least Privilege** ✅ |

## Testing Results

```bash
# Original container
$ docker exec streaklet whoami
root

# Hardened container
$ docker exec streaklet-hardened whoami
appuser
```

## Usage

### Build Hardened Image
```bash
docker build -f Dockerfile.hardened -t streaklet:hardened .
```

### Run Hardened Container
```bash
docker run -d \
  --name streaklet \
  -p 8080:8080 \
  -v ./data:/data \
  -e APP_TIMEZONE=America/Chicago \
  -e DB_PATH=/data/app.db \
  -e APP_SECRET_KEY=your_secret_key \
  streaklet:hardened
```

### Using with Docker Compose
Update `docker-compose.yml`:
```yaml
services:
  streaklet:
    build:
      context: .
      dockerfile: Dockerfile.hardened  # <-- Changed this line
    # ... rest of config
```

## Remaining Hardening Options

For even more security, consider:

### 1. **Read-Only Filesystem**
Add to docker-compose.yml:
```yaml
read_only: true
tmpfs:
  - /tmp
```

### 2. **Drop Capabilities**
```yaml
cap_drop:
  - ALL
cap_add:
  - CHOWN  # Only if needed
  - SETUID
  - SETGID
```

### 3. **Resource Limits**
```yaml
deploy:
  resources:
    limits:
      cpus: '1.0'
      memory: 512M
```

### 4. **Pin Base Image with Digest**
```dockerfile
FROM python:3.12-slim@sha256:abc123...
```

### 5. **Vulnerability Scanning**
```bash
# Using Docker Scout
docker scout cves streaklet:hardened

# Or Trivy
trivy image streaklet:hardened
```

## Security Best Practices Applied

- ✅ Multi-stage builds
- ✅ Non-root user
- ✅ Minimal base image (slim variant)
- ✅ No build tools in production
- ✅ Proper file ownership
- ✅ Health checks
- ✅ No package manager cache
- ✅ Explicit user creation with fixed UID/GID
- ✅ Security labels

## Migration Path

1. **Test:** Build and test hardened image locally
2. **Compare:** Run both versions side-by-side
3. **Verify:** Ensure permissions work with mounted volumes
4. **Switch:** Update docker-compose.yml to use Dockerfile.hardened
5. **Monitor:** Watch logs for permission issues

## Volume Permissions Note

Since the container now runs as `appuser` (uid 1000), ensure your host volume has correct permissions:

```bash
# Option 1: Match host user to container user
chown -R 1000:1000 ./data

# Option 2: Make writable by all (less secure)
chmod 777 ./data
```

## Additional Resources

- [Docker Security Best Practices](https://docs.docker.com/develop/security-best-practices/)
- [OWASP Docker Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Docker_Security_Cheat_Sheet.html)
- [CIS Docker Benchmark](https://www.cisecurity.org/benchmark/docker)
