"""
FlowGrid - Main Application Entrypoint
======================================
Core entry point for the FastAPI backend service. Configures structured logging,
security headers, CORS middleware, global exception handlers, OpenAPI documentation,
and modular sub-routers.
"""

import time
from typing import Dict, Any
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.db.session import check_db_connection
from app.api.v1.api import api_router

# ------------------------------------------------------------------------------
# 1. Logging Initialization
# ------------------------------------------------------------------------------
setup_logging(settings.log_level)
logger = get_logger("main")

# ------------------------------------------------------------------------------
# 2. OpenAPI Documentation Metadata
# ------------------------------------------------------------------------------
OPENAPI_DESCRIPTION = """
### FlowGrid Logistics & Supply Chain Platform API

FlowGrid delivers enterprise-grade freight dispatch, real-time tracking,
warehouse storage optimization, inventory management, and route planning.

#### Key Functional Modules
* **Authentication**: Token generation, role-based authorization (ADMIN, MANAGER, DRIVER, VIEWER).
* **Warehouses**: Physical fulfillment hubs, square footage capacity, and active status tracking.
* **Products**: Commercial catalog items, SKUs, and unit pricing.
* **Inventory**: Stock-on-hand tracking, safety thresholds, and reorder levels.
* **Drivers**: Logistics personnel, license credentials, and dispatch readiness.
* **Vehicles**: Freight transport units, vehicle types, and gross carrying capacity.
* **Shipments**: Comprehensive freight lifecycle management with state machine governance.
* **Routes**: Transit corridors, origin-destination waypoints, and shipment allocations.
* **Analytics**: Real-time operational KPIs, daily throughput, inventory alerts, and corridor utilization.

#### Authentication & Authorization
All secured endpoints require an HTTP Bearer JWT token passed via the `Authorization` header:
```http
Authorization: Bearer <access_token>
```
"""

OPENAPI_TAGS = [
    {
        "name": "Authentication",
        "description": "User registration, authentication, credential validation, and JWT token issuance.",
    },
    {
        "name": "Warehouses",
        "description": "Physical fulfillment centers, storage capacities, and operational status.",
    },
    {
        "name": "Products",
        "description": "Commercial catalog items, SKUs, product pricing, and descriptions.",
    },
    {
        "name": "Inventory",
        "description": "On-hand stock balances, safety threshold tracking, and replenishment alerts.",
    },
    {
        "name": "Drivers",
        "description": "Logistics field personnel records, commercial licenses, and dispatch status.",
    },
    {
        "name": "Vehicles",
        "description": "Fleet transport units, carrying capacities, and operational availability.",
    },
    {
        "name": "Shipments",
        "description": "Commercial cargo lifecycle dispatch, waypoint tracking, and state machine transitions.",
    },
    {
        "name": "Routes",
        "description": "Transportation corridors, route definitions, and multi-shipment allocations.",
    },
    {
        "name": "Analytics",
        "description": "Executive dashboard KPIs, throughput metrics, inventory health, and route performance.",
    },
    {
        "name": "System",
        "description": "Operational health probes and database connectivity verification.",
    },
]

# ------------------------------------------------------------------------------
# 3. FastAPI Application Initialization
# ------------------------------------------------------------------------------
app = FastAPI(
    title="FlowGrid API",
    version=settings.app_version,
    description=OPENAPI_DESCRIPTION,
    openapi_tags=OPENAPI_TAGS,
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "FlowGrid Engineering",
        "url": "https://github.com/sakshishewale01/FlowGrid",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    swagger_ui_parameters={
        "persistAuthorization": True,
        "displayRequestDuration": True,
        "filter": True,
    },
)

# ------------------------------------------------------------------------------
# 4. Security Headers & Request Timing Middleware
# ------------------------------------------------------------------------------
@app.middleware("http")
async def security_and_timing_middleware(request: Request, call_next):
    """
    Measures request latency, logs inbound calls, and injects production security headers.
    """
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time_ms = (time.perf_counter() - start_time) * 1000.0

    # Inject HTTP security hardening headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["X-Process-Time-Ms"] = f"{process_time_ms:.2f}"

    if not settings.debug:
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )

    # Log non-health requests
    if not request.url.path.startswith("/health"):
        logger.info(
            "%s %s -> %s (%.2fms)",
            request.method,
            request.url.path,
            response.status_code,
            process_time_ms,
        )

    return response

# ------------------------------------------------------------------------------
# 5. CORS (Cross-Origin Resource Sharing) Configuration
# ------------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------------------
# 6. Global Exception Handlers (Prevent Data & Stack Trace Leakage)
# ------------------------------------------------------------------------------
@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """
    Intercepts unhandled database errors and logs full details internally
    while returning a sanitized HTTP 500 error to clients.
    """
    logger.error("Unhandled database error on %s %s: %s", request.method, request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "A database error occurred while processing your request."},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """
    Catch-all exception handler to prevent unhandled runtime errors from
    exposing internal server traces, Python paths, or stack frames.
    """
    logger.critical("Unhandled server exception on %s %s: %s", request.method, request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected internal server error occurred."},
    )

# ------------------------------------------------------------------------------
# 7. Router Registration
# ------------------------------------------------------------------------------
app.include_router(api_router, prefix="/api/v1")

from app.api.v1.endpoints.ws_tracking import router as ws_tracking_router
app.include_router(ws_tracking_router)


# ------------------------------------------------------------------------------
# 8. Base & Health Endpoints
# ------------------------------------------------------------------------------
@app.get(
    "/health",
    tags=["System"],
    summary="Health check endpoint",
    response_description="Returns operational health status of the application",
)
def health_check() -> Dict[str, str]:
    """
    Standard application health check probe for load balancers and container orchestrators.
    """
    return {
        "status": "healthy",
        "application": "FlowGrid",
    }


@app.get(
    "/health/db",
    tags=["System"],
    summary="Database connectivity check",
    response_description="Returns database connectivity status and diagnostic summary",
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
