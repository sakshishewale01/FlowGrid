"""
Proof of Delivery Repository
============================
Persistence operations for delivery confirmations.
"""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.delivery_confirmation import DeliveryConfirmation


class DeliveryConfirmationRepository:
    @staticmethod
    def get_by_shipment_id(
        db: Session,
        shipment_id: int,
    ) -> Optional[DeliveryConfirmation]:
        return db.scalars(
            select(DeliveryConfirmation).where(
                DeliveryConfirmation.shipment_id == shipment_id
            )
        ).first()

    @staticmethod
    def list_all(
        db: Session,
        skip: int = 0,
        limit: int = 100,
    ) -> List[DeliveryConfirmation]:
        stmt = (
            select(DeliveryConfirmation)
            .order_by(DeliveryConfirmation.delivered_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(db.scalars(stmt).all())


delivery_confirmation_repository = DeliveryConfirmationRepository()
