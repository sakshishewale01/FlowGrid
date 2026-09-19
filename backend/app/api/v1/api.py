"""
API v1 Router Aggregator
========================
Aggregates and registers all modular sub-routers for API version 1.
"""

from fastapi import APIRouter
from app.api.v1.endpoints import auth, warehouses, products

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
