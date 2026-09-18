"""
Vehicle Model
=============
Represents transport vehicles, trucks, and fleet units in the logistics network.
"""

from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Numeric, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Vehicle(Base):
    """
    SQLAlchemy ORM model for the `vehicles` table.
    Tracks freight vehicles, registration numbers, carrying capacity, and maintenance status.
    """
    __tablename__ = "vehicles"

    # Primary Key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Vehicle identification
    registration_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )  # License plate or fleet identifier (e.g., 'UNIT-402')
    vehicle_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # e.g., 'Van', 'Semi-Trailer', 'Refrigerated Truck'
    capacity: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )  # Maximum weight capacity in kilograms (kg)
    status: Mapped[str] = mapped_column(
        String(20),
        default="AVAILABLE",
        nullable=False,
    )  # e.g., 'AVAILABLE', 'IN_USE', 'MAINTENANCE', 'DECOMMISSIONED'

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

    def __repr__(self) -> str:
        return f"<Vehicle id={self.id} reg='{self.registration_number}' type='{self.vehicle_type}' status='{self.status}'>"
