"""
Shipment Model
==============
Represents commercial cargo, freight dispatches, and packages in the FlowGrid platform.
Governed by a strict state machine lifecycle from CREATED to DELIVERED.
"""

from datetime import datetime
from decimal import Decimal
import enum
from typing import Optional, TYPE_CHECKING, List
from sqlalchemy import (
    String,
    Boolean,
    DateTime,
    Numeric,
    ForeignKey,
    Enum as SQLEnum,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.warehouse import Warehouse
    from app.models.driver import Driver
    from app.models.vehicle import Vehicle
    from app.models.tracking import ShipmentStatusHistory, ShipmentTrackingEvent
    from app.models.route import Route, RouteShipment



class ShipmentStatus(str, enum.Enum):
    """
    Allowed states in the FlowGrid shipment state machine lifecycle.
    """
    CREATED = "CREATED"
    CONFIRMED = "CONFIRMED"
    ASSIGNED = "ASSIGNED"
    PICKED_UP = "PICKED_UP"
    IN_TRANSIT = "IN_TRANSIT"
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"
    RETURNED = "RETURNED"


class Shipment(Base):
    """
    SQLAlchemy ORM model for the `shipments` table.
    """
    __tablename__ = "shipments"

    # Primary Key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Unique Tracking Identification
    tracking_number: Mapped[str] = mapped_column(
        String(60),
        unique=True,
        index=True,
        nullable=False,
    )

    # Logistics Node Relationships
    origin_warehouse_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("warehouses.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Consignee Destination Details
    destination_address: Mapped[str] = mapped_column(String(255), nullable=False)
    destination_city: Mapped[str] = mapped_column(String(100), nullable=False)
    destination_state: Mapped[str] = mapped_column(String(100), nullable=False)
    destination_postal_code: Mapped[str] = mapped_column(String(20), nullable=False)

    # Lifecycle State
    status: Mapped[ShipmentStatus] = mapped_column(
        SQLEnum(ShipmentStatus, name="shipment_status_enum", native_enum=True),
        default=ShipmentStatus.CREATED,
        nullable=False,
        index=True,
    )

    # Fleet Allocation
    assigned_driver_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("drivers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    assigned_vehicle_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("vehicles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Cargo Dimensions and Weight
    total_weight_kg: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )
    total_volume_cbm: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )

    # Operational Schedule & Timestamps
    scheduled_pickup_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    delivered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Soft Deletion Flag
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Audit Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    origin_warehouse: Mapped[Optional["Warehouse"]] = relationship("Warehouse")
    assigned_driver: Mapped[Optional["Driver"]] = relationship("Driver")
    assigned_vehicle: Mapped[Optional["Vehicle"]] = relationship("Vehicle")
    status_history: Mapped[List["ShipmentStatusHistory"]] = relationship(
        "ShipmentStatusHistory",
        back_populates="shipment",
        cascade="all, delete-orphan",
        order_by="desc(ShipmentStatusHistory.created_at)",
    )
    tracking_events: Mapped[List["ShipmentTrackingEvent"]] = relationship(
        "ShipmentTrackingEvent",
        back_populates="shipment",
        cascade="all, delete-orphan",
        order_by="desc(ShipmentTrackingEvent.timestamp)",
    )
    route_shipments: Mapped[List["RouteShipment"]] = relationship(
        "RouteShipment",
        back_populates="shipment",
        cascade="all, delete-orphan",
        order_by="desc(RouteShipment.assigned_at)",
    )
    routes: Mapped[List["Route"]] = relationship(
        "Route",
        secondary="route_shipments",
        back_populates="shipments",
        viewonly=True,
    )

    def __repr__(self) -> str:
        return f"<Shipment id={self.id} tracking='{self.tracking_number}' status='{self.status.value}'>"
