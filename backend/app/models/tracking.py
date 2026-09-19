"""
Shipment Tracking and Status History Models
============================================
Defines persistent audit records for shipment lifecycle status changes
and granular logistics tracking events (checkpoints, scans, carrier milestones).
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    Enum as SQLEnum,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.shipment import ShipmentStatus

if TYPE_CHECKING:
    from app.models.shipment import Shipment
    from app.models.user import User


class ShipmentStatusHistory(Base):
    """
    Persistent audit trail of all shipment lifecycle state machine transitions.
    Records who triggered the transition, previous/new status, timestamp, and remarks.
    """
    __tablename__ = "shipment_status_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    shipment_id: Mapped[int] = mapped_column(
        ForeignKey("shipments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    previous_status: Mapped[Optional[ShipmentStatus]] = mapped_column(
        SQLEnum(ShipmentStatus, name="shipment_status_enum", create_type=False, native_enum=True),
        nullable=True,
        index=True,
    )

    new_status: Mapped[ShipmentStatus] = mapped_column(
        SQLEnum(ShipmentStatus, name="shipment_status_enum", create_type=False, native_enum=True),
        nullable=False,
        index=True,
    )


    changed_by_user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    remarks: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Relationships
    shipment: Mapped["Shipment"] = relationship("Shipment", back_populates="status_history")
    changed_by: Mapped[Optional["User"]] = relationship("User")

    def __repr__(self) -> str:
        return (
            f"<ShipmentStatusHistory id={self.id} shipment_id={self.shipment_id} "
            f"from={self.previous_status} to={self.new_status}>"
        )


class ShipmentTrackingEvent(Base):
    """
    Granular physical and operational tracking milestones for a shipment
    (e.g., checkpoints, sorting facility arrival, out for delivery dispatch).
    """
    __tablename__ = "shipment_tracking_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    shipment_id: Mapped[int] = mapped_column(
        ForeignKey("shipments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    created_by_user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    shipment: Mapped["Shipment"] = relationship("Shipment", back_populates="tracking_events")
    created_by: Mapped[Optional["User"]] = relationship("User")

    def __repr__(self) -> str:
        return (
            f"<ShipmentTrackingEvent id={self.id} shipment_id={self.shipment_id} "
            f"type='{self.event_type}' location='{self.location}'>"
        )
