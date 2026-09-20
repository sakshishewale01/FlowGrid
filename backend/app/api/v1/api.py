"""
API v1 Router Aggregator
========================
Aggregates and registers all modular sub-routers for API version 1.
"""

from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    warehouses,
    products,
    inventory,
    drivers,
    vehicles,
    shipments,
    routes,
)

api_router = APIRouter()

# Register authentication endpoints under /auth
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"],
)

# Register warehouse endpoints under /warehouses
api_router.include_router(
    warehouses.router,
    prefix="/warehouses",
    tags=["Warehouses"],
)

# Register product endpoints under /products
api_router.include_router(
    products.router,
    prefix="/products",
    tags=["Products"],
)

# Register inventory endpoints under /inventory
api_router.include_router(
    inventory.router,
    prefix="/inventory",
    tags=["Inventory"],
)

# Register driver endpoints under /drivers
api_router.include_router(
    drivers.router,
    prefix="/drivers",
    tags=["Drivers"],
)

# Register vehicle endpoints under /vehicles
api_router.include_router(
    vehicles.router,
    prefix="/vehicles",
    tags=["Vehicles"],
)

# Register shipment endpoints under /shipments
api_router.include_router(
    shipments.router,
    prefix="/shipments",
    tags=["Shipments"],
)

# Register route endpoints under /routes
api_router.include_router(
    routes.router,
    prefix="/routes",
    tags=["Routes"],
)
