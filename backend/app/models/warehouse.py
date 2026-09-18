"""
Warehouse Model
===============
Represents physical logistics fulfillment hubs, transit depots, and distribution centers.
"""

from datetime import datetime
from typing import List, TYPE_CHECKING
from sqlalchemy import String, Integer, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.inventory import Inventory


class Warehouse(Base):
    """
    SQLAlchemy ORM model for the `warehouses` table.
    """
    __tablename__ = "warehouses"

    # Primary Key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Warehouse attributes
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    location: Mapped[str] = mapped_column(String(150), nullable=False)  # e.g., "Chicago, IL"
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)  # Storage capacity (e.g. sq ft)
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
    # One warehouse holds many inventory stock records
    inventories: Mapped[List["Inventory"]] = relationship(
        "Inventory",
        back_populates="warehouse",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Warehouse id={self.id} name='{self.name}' location='{self.location}'>"
