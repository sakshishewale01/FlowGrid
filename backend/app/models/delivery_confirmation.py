"""
Proof of Delivery Model
=======================
Stores the immutable confirmation details submitted when a shipment is delivered.
Evidence is metadata only; this model does not provide file upload or storage.
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.shipment import Shipment
    from app.models.user import User


class DeliveryConfirmation(Base):
    """One-to-one proof-of-delivery confirmation for a shipment."""

    __tablename__ = "delivery_confirmations"
    __table_args__ = (
        UniqueConstraint("shipment_id", name="uq_delivery_confirmations_shipment_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    shipment_id: Mapped[int] = mapped_column(
        ForeignKey("shipments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    submitted_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    recipient_name: Mapped[str] = mapped_column(String(150), nullable=False)
    delivered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    delivery_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evidence_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    shipment: Mapped["Shipment"] = relationship(
        "Shipment",
        back_populates="delivery_confirmation",
    )
    submitted_by: Mapped["User"] = relationship("User")

    def __repr__(self) -> str:
        return (
            f"<DeliveryConfirmation id={self.id} shipment_id={self.shipment_id} "
            f"recipient='{self.recipient_name}'>"
        )
