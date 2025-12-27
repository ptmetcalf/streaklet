# ==============================================================================
# Multi-Stage Build: Stage 1 - Builder (build dependencies isolated here)
# ==============================================================================
FROM python:3.12-slim AS builder

# Set working directory
WORKDIR /app

# Install build dependencies (gcc needed for some Python packages)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install to user site-packages
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# ==============================================================================
# Stage 2 - Runtime (minimal, no build tools)
# ==============================================================================
FROM python:3.12-slim

# Security labels
LABEL maintainer="Streaklet" \
      description="Hardened Streaklet habit tracker" \
      security.hardened="true"

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/home/appuser/.local/bin:$PATH"

# Create non-root user with specific UID/GID for consistency
RUN groupadd -r appuser -g 1000 && \
    useradd -r -u 1000 -g appuser -m -s /sbin/nologin appuser

# Copy installed packages from builder stage
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local

# Copy application code with proper ownership
COPY --chown=appuser:appuser . .

# Create data directory with proper permissions
RUN mkdir -p /data && \
    chown -R appuser:appuser /data

# Create entrypoint script with proper ownership
RUN echo '#!/bin/sh\n\
set -e\n\
echo "Running database migrations..."\n\
alembic upgrade head\n\
echo "Starting application..."\n\
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080} --log-level info\n\
' > /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh && \
    chown appuser:appuser /app/entrypoint.sh

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
