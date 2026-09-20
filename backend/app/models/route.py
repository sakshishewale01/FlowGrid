"""
Route and RouteShipment Models
==============================
Represents transportation corridors, multi-stop delivery routes, and shipment allocations.
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
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.shipment import Shipment
    from app.models.user import User


class RouteStatus(str, enum.Enum):
    """
    Operational lifecycle status of a logistics route.
    """
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    PLANNED = "PLANNED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class Route(Base):
    """
    SQLAlchemy ORM model for the `routes` table.
    Tracks transit corridors, origins, destinations, distances, durations, and status.
    """
    __tablename__ = "routes"

    # Primary Key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Route Identification
    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True,
    )

    # Origin & Destination Waypoints
    origin: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    destination: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    # Operational Logistics Metrics
    estimated_distance: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )
    estimated_duration: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )

    # Status & Soft Delete Flag
    status: Mapped[RouteStatus] = mapped_column(
        SQLEnum(RouteStatus, name="route_status_enum", native_enum=False),
        default=RouteStatus.ACTIVE,
        nullable=False,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
    )

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
    route_shipments: Mapped[List["RouteShipment"]] = relationship(
        "RouteShipment",
        back_populates="route",
        cascade="all, delete-orphan",
        order_by="desc(RouteShipment.assigned_at)",
    )
    shipments: Mapped[List["Shipment"]] = relationship(
        "Shipment",
        secondary="route_shipments",
        back_populates="routes",
        viewonly=True,
    )

    def __repr__(self) -> str:
        return f"<Route id={self.id} name='{self.name}' status='{self.status.value}'>"


class RouteShipment(Base):
    """
    Association table linking shipments to assigned routes.
    Maintains foreign keys, assignment timestamps, and uniqueness constraints.
    """
    __tablename__ = "route_shipments"
    __table_args__ = (
        UniqueConstraint("route_id", "shipment_id", name="uq_route_shipment"),
    )

    # Primary Key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Foreign Keys
    route_id: Mapped[int] = mapped_column(
        ForeignKey("routes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    shipment_id: Mapped[int] = mapped_column(
        ForeignKey("shipments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Assignment Metadata
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    assigned_by_user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Relationships
    route: Mapped["Route"] = relationship("Route", back_populates="route_shipments")
    shipment: Mapped["Shipment"] = relationship("Shipment", back_populates="route_shipments")
    assigned_by_user: Mapped[Optional["User"]] = relationship("User")

    def __repr__(self) -> str:
        return f"<RouteShipment id={self.id} route_id={self.route_id} shipment_id={self.shipment_id}>"
