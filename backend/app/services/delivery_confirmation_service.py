"""
Proof of Delivery Service
=========================
Creates immutable delivery confirmations and completes shipments atomically.
"""

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.delivery_confirmation import DeliveryConfirmation
from app.models.shipment import Shipment, ShipmentStatus
from app.models.tracking import ShipmentStatusHistory
from app.models.user import User, UserRole
from app.repositories.delivery_confirmation_repository import (
    delivery_confirmation_repository,
)
from app.repositories.shipment_repository import shipment_repository
from app.schemas.delivery_confirmation import DeliveryConfirmationCreate
from app.services.shipment_service import ALLOWED_TRANSITIONS


class DeliveryConfirmationService:
    def __init__(
        self,
        confirmation_repo=delivery_confirmation_repository,
        shipment_repo=shipment_repository,
    ):
        self.confirmation_repo = confirmation_repo
        self.shipment_repo = shipment_repo

    def _get_shipment(self, db: Session, shipment_id: int) -> Shipment:
        shipment = self.shipment_repo.get_by_id(db, shipment_id)
        if not shipment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Shipment with ID {shipment_id} was not found",
            )
        return shipment

    @staticmethod
    def _can_submit(shipment: Shipment, current_user: User) -> bool:
        if current_user.role in (UserRole.ADMIN, UserRole.MANAGER):
            return True
        return bool(
            current_user.role == UserRole.DRIVER
            and current_user.driver
            and shipment.assigned_driver_id == current_user.driver.id
        )

    def create_confirmation(
        self,
        db: Session,
        shipment_id: int,
        payload: DeliveryConfirmationCreate,
        current_user: User,
    ) -> DeliveryConfirmation:
        shipment = self._get_shipment(db, shipment_id)
        if not self._can_submit(shipment, current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the assigned driver or an authorized manager/admin can confirm delivery",
            )

        if self.confirmation_repo.get_by_shipment_id(db, shipment_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A delivery confirmation already exists for this shipment",
            )

        if shipment.status != ShipmentStatus.OUT_FOR_DELIVERY:
            allowed = ALLOWED_TRANSITIONS.get(shipment.status, set())
            allowed_names = ", ".join(item.value for item in allowed) or "None"
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Delivery confirmation requires OUT_FOR_DELIVERY status; "
                    f"current status is '{shipment.status.value}'. Permitted transitions: {allowed_names}"
                ),
            )

        confirmation = DeliveryConfirmation(
            shipment_id=shipment.id,
            submitted_by_user_id=current_user.id,
            recipient_name=payload.recipient_name,
            delivered_at=payload.delivered_at,
            delivery_notes=payload.delivery_notes,
            evidence_metadata=payload.evidence_metadata,
        )
        history = ShipmentStatusHistory(
            shipment_id=shipment.id,
            previous_status=shipment.status,
            new_status=ShipmentStatus.DELIVERED,
            changed_by_user_id=current_user.id,
            remarks=payload.delivery_notes,
            created_at=datetime.now(timezone.utc),
        )

        try:
            shipment.status = ShipmentStatus.DELIVERED
            shipment.delivered_at = payload.delivered_at
            db.add(confirmation)
            db.add(history)
            db.commit()
            db.refresh(confirmation)
            return confirmation
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A delivery confirmation already exists for this shipment",
            )
        except Exception:
            db.rollback()
            raise

    def get_confirmation(
        self,
        db: Session,
        shipment_id: int,
    ) -> DeliveryConfirmation:
        self._get_shipment(db, shipment_id)
        confirmation = self.confirmation_repo.get_by_shipment_id(db, shipment_id)
        if not confirmation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No delivery confirmation exists for this shipment",
            )
        return confirmation

    def list_confirmations(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
    ) -> List[DeliveryConfirmation]:
        return self.confirmation_repo.list_all(db, skip=skip, limit=limit)

    def list_delivered_without_confirmation(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Shipment]:
        from sqlalchemy import select

        stmt = (
            select(Shipment)
            .outerjoin(
                DeliveryConfirmation,
                DeliveryConfirmation.shipment_id == Shipment.id,
            )
            .where(
                Shipment.status == ShipmentStatus.DELIVERED,
                DeliveryConfirmation.id.is_(None),
            )
            .order_by(Shipment.delivered_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(db.scalars(stmt).all())


delivery_confirmation_service = DeliveryConfirmationService()
