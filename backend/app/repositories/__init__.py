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
from app.repositories.inventory_repository import (
    InventoryRepository,
    inventory_repository,
)
from app.repositories.driver_repository import (
    DriverRepository,
    driver_repository,
)
from app.repositories.vehicle_repository import (
    VehicleRepository,
    vehicle_repository,
)
from app.repositories.shipment_repository import (
    ShipmentRepository,
    shipment_repository,
)

__all__ = [
    "WarehouseRepository",
    "warehouse_repository",
    "ProductRepository",
    "product_repository",
    "InventoryRepository",
    "inventory_repository",
    "DriverRepository",
    "driver_repository",
    "VehicleRepository",
    "vehicle_repository",
    "ShipmentRepository",
    "shipment_repository",
]
