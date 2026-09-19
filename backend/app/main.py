"""
FlowGrid - Main Application Entrypoint
======================================
This is the core entry point for the FastAPI backend service.

When starting the server using:
    uvicorn app.main:app --reload
Uvicorn looks inside this file (`main.py`) for the FastAPI instance variable named `app`.
"""

from typing import Dict, Any
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.session import check_db_connection
from app.api.v1.api import api_router

# ------------------------------------------------------------------------------
# 1. FastAPI Application Initialization
# ------------------------------------------------------------------------------
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Intelligent Logistics and Supply Chain Management Platform API",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ------------------------------------------------------------------------------
# 2. CORS (Cross-Origin Resource Sharing) Configuration
# ------------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------------------
# 3. Router Registration
# ------------------------------------------------------------------------------
app.include_router(api_router, prefix="/api/v1")


# ------------------------------------------------------------------------------
# 3. Base & Health Endpoints
# ------------------------------------------------------------------------------
@app.get(
    "/health",
    tags=["System"],
    summary="Health check endpoint",
    response_description="Returns the operational health status of the application",
)
def health_check() -> Dict[str, str]:
    """
    Standard application health check endpoint.
    Used by container orchestrators (e.g., AWS ECS, Kubernetes), load balancers,
    and frontend dashboards to confirm the backend process is healthy.
    """
    return {
        "status": "healthy",
        "application": "FlowGrid",
    }


@app.get(
    "/health/db",
    tags=["System"],
    summary="Database connectivity check",
    response_description="Returns the connectivity status to the PostgreSQL database",
)
def database_health_check() -> Dict[str, Any]:
    """
    Executes a safe 'SELECT 1' test query against the database engine.
    Does not raise unhandled exceptions; returns connection status and diagnostic message.
    """
    is_connected, message = check_db_connection()
    return {
        "status": "connected" if is_connected else "disconnected",
        "database_connected": is_connected,
        "detail": message,
    }


@app.get(
    "/",
    tags=["System"],
    summary="Root greeting and API discovery",
)
def root_endpoint() -> Dict[str, str]:
    """
    Root endpoint offering a welcome message and links to interactive API documentation.
    """
    return {
        "application": settings.app_name,
        "version": settings.app_version,
        "environment": settings.app_env,
        "message": "Welcome to FlowGrid API. Visit /docs for the interactive OpenAPI documentation.",
    }
