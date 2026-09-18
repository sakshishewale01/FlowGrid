"""
Inventory Model
===============
Represents on-hand stock levels and reorder thresholds of a product at a specific warehouse.
"""

from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import Integer, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.warehouse import Warehouse
    from app.models.product import Product


class Inventory(Base):
    """
    SQLAlchemy ORM model for the `inventories` table.
    Links a Product to a Warehouse with quantity balances.
    """
    __tablename__ = "inventories"
    __table_args__ = (
        # A warehouse cannot have duplicate inventory rows for the same product
        UniqueConstraint("warehouse_id", "product_id", name="uq_warehouse_product"),
    )

    # Primary Key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Foreign Keys
    warehouse_id: Mapped[int] = mapped_column(
        ForeignKey("warehouses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Stock metrics
    quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reorder_level: Mapped[int] = mapped_column(Integer, default=10, nullable=False)

    # Audit Timestamp
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    warehouse: Mapped["Warehouse"] = relationship("Warehouse", back_populates="inventories")
    product: Mapped["Product"] = relationship("Product", back_populates="inventories")

    def __repr__(self) -> str:
        return f"<Inventory id={self.id} warehouse_id={self.warehouse_id} product_id={self.product_id} qty={self.quantity}>"
