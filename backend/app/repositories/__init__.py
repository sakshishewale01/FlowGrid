"""
Repositories Package
====================
Encapsulates database access operations and queries using SQLAlchemy.
"""

from app.repositories.warehouse_repository import (
    WarehouseRepository,
    warehouse_repository,
)
from app.repositories.product_repository import (
    ProductRepository,
    product_repository,
)

__all__ = [
    "WarehouseRepository",
    "warehouse_repository",
    "ProductRepository",
    "product_repository",
]
