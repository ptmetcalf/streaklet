FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p /data

# Expose port
EXPOSE 8080

# Create entrypoint script for migrations + app startup
RUN echo '#!/bin/bash\n\
set -e\n\
echo "Running database migrations..."\n\
alembic upgrade head\n\
echo "Starting application..."\n\
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}\n\
' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
