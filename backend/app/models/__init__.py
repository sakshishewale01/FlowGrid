"""
FlowGrid Models Package
=======================
Central export for all SQLAlchemy 2.0 database models.
Importing this package registers all models with `Base.metadata`.
"""

from app.models.user import User, UserRole
from app.models.warehouse import Warehouse
from app.models.product import Product
from app.models.inventory import Inventory
from app.models.driver import Driver
from app.models.vehicle import Vehicle
from app.models.shipment import Shipment, ShipmentStatus
from app.models.tracking import ShipmentStatusHistory, ShipmentTrackingEvent
from app.models.route import Route, RouteStatus, RouteShipment

__all__ = [
    "User",
    "UserRole",
    "Warehouse",
    "Product",
    "Inventory",
    "Driver",
    "Vehicle",
    "Shipment",
    "ShipmentStatus",
    "ShipmentStatusHistory",
    "ShipmentTrackingEvent",
    "Route",
    "RouteStatus",
    "RouteShipment",
]

