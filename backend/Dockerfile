# ==============================================================================
# FlowGrid Backend - Production Dockerfile
# ==============================================================================
# Multi-stage production container image running FastAPI with Uvicorn workers
# and a non-root security context.
# ==============================================================================

FROM python:3.12-slim AS base

# Prevent Python from writing .pyc files and enable unbuffered stdout/stderr logging
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=8000

# Install curl for container health check probe
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create a dedicated non-root application user and group
RUN groupadd -g 1001 flowgrid && \
    useradd -u 1001 -g flowgrid -s /bin/bash -m flowgrid

WORKDIR /app

# Copy dependency specifications first to leverage Docker layer caching
COPY requirements.txt .

# Install dependencies into system Python environment
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code, migrations, scripts, and ML inference artifact
COPY --chown=flowgrid:flowgrid app/ app/
COPY --chown=flowgrid:flowgrid alembic/ alembic/
COPY --chown=flowgrid:flowgrid scripts/ scripts/
COPY --chown=flowgrid:flowgrid ml/ ml/
COPY --chown=flowgrid:flowgrid ml_data/ ml_data/
COPY --chown=flowgrid:flowgrid alembic.ini .
COPY --chown=flowgrid:flowgrid docker-entrypoint.sh .

# Run the entrypoint as a non-root user while retaining the image's root-owned layers
RUN chmod 755 docker-entrypoint.sh

# Switch to the non-root user for execution security
USER flowgrid

# Expose standard FastAPI service port
EXPOSE 8000

# Health check probe monitoring container readiness
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Apply versioned schema migrations before starting application workers
ENTRYPOINT ["./docker-entrypoint.sh"]

# Production startup command utilizing 4 Uvicorn worker processes
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
