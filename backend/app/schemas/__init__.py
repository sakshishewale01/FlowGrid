"""
FlowGrid Schemas Package
========================
Exports Pydantic validation schemas for API requests and serialized responses.
"""

from app.schemas.user import UserResponse
from app.schemas.auth import UserRegisterRequest, UserLoginRequest, TokenResponse
from app.schemas.warehouse import (
    WarehouseBase,
    WarehouseCreate,
    WarehouseUpdate,
    WarehouseResponse,
)
from app.schemas.product import (
    ProductBase,
    ProductCreate,
    ProductUpdate,
    ProductResponse,
)
from app.schemas.inventory import (
    InventoryBase,
    InventoryCreate,
    InventoryUpdate,
    InventoryResponse,
    WarehouseSummary,
    ProductSummary,
)
from app.schemas.driver import (
    DriverBase,
    DriverCreate,
    DriverUpdate,
    DriverResponse,
    UserDriverSummary,
)
from app.schemas.vehicle import (
    VehicleBase,
    VehicleCreate,
    VehicleUpdate,
    VehicleResponse,
)
from app.schemas.shipment import (
    ShipmentBase,
    ShipmentCreate,
    ShipmentUpdate,
    ShipmentStatusUpdate,
    ShipmentResponse,
    WarehouseShipmentSummary,
    DriverShipmentSummary,
    VehicleShipmentSummary,
)

__all__ = [
    "UserResponse",
    "UserRegisterRequest",
    "UserLoginRequest",
    "TokenResponse",
    "WarehouseBase",
    "WarehouseCreate",
    "WarehouseUpdate",
    "WarehouseResponse",
    "ProductBase",
    "ProductCreate",
    "ProductUpdate",
    "ProductResponse",
    "InventoryBase",
    "InventoryCreate",
    "InventoryUpdate",
    "InventoryResponse",
    "WarehouseSummary",
    "ProductSummary",
    "DriverBase",
    "DriverCreate",
    "DriverUpdate",
    "DriverResponse",
    "UserDriverSummary",
    "VehicleBase",
    "VehicleCreate",
    "VehicleUpdate",
    "VehicleResponse",
    "ShipmentBase",
    "ShipmentCreate",
    "ShipmentUpdate",
    "ShipmentStatusUpdate",
    "ShipmentResponse",
    "WarehouseShipmentSummary",
    "DriverShipmentSummary",
    "VehicleShipmentSummary",
]
