"""
Shipment Repository
===================
Encapsulates all database query and persistence operations for the Shipment model.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy import select, func
from sqlalchemy.orm import Session, joinedload

from app.models.shipment import Shipment, ShipmentStatus


class ShipmentRepository:
    """
    Data access layer for Shipment logistics records.
    """

    @staticmethod
    def get_by_id(db: Session, shipment_id: int) -> Optional[Shipment]:
        """
        Retrieves a shipment by primary key ID, eagerly loading linked nodes.
        """
        stmt = (
            select(Shipment)
            .options(
                joinedload(Shipment.origin_warehouse),
                joinedload(Shipment.assigned_driver),
                joinedload(Shipment.assigned_vehicle),
            )
            .where(Shipment.id == shipment_id)
        )
        return db.scalars(stmt).first()

    @staticmethod
    def get_by_tracking_number(
        db: Session,
        tracking_number: str,
    ) -> Optional[Shipment]:
        """
        Retrieves a shipment by its unique tracking number using normalized uppercase match.
        """
        normalized = tracking_number.strip().upper()
        stmt = (
            select(Shipment)
            .options(
                joinedload(Shipment.origin_warehouse),
                joinedload(Shipment.assigned_driver),
                joinedload(Shipment.assigned_vehicle),
            )
            .where(func.upper(func.trim(Shipment.tracking_number)) == normalized)
        )
        return db.scalars(stmt).first()

    @staticmethod
    def get_all(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status: Optional[ShipmentStatus] = None,
        tracking_number: Optional[str] = None,
        origin_warehouse_id: Optional[int] = None,
        is_active: Optional[bool] = None,
    ) -> List[Shipment]:
        """
        Retrieves a paginated list of shipments with optional filtering.
        """
        stmt = (
            select(Shipment)
            .options(
                joinedload(Shipment.origin_warehouse),
                joinedload(Shipment.assigned_driver),
                joinedload(Shipment.assigned_vehicle),
            )
        )

        if status is not None:
            stmt = stmt.where(Shipment.status == status)

        if tracking_number:
            normalized = tracking_number.strip().upper()
            stmt = stmt.where(
                func.upper(Shipment.tracking_number).contains(normalized)
            )

        if origin_warehouse_id is not None:
            stmt = stmt.where(Shipment.origin_warehouse_id == origin_warehouse_id)

        if is_active is not None:
            stmt = stmt.where(Shipment.is_active == is_active)

        stmt = stmt.offset(skip).limit(limit).order_by(Shipment.id.asc())
        return list(db.scalars(stmt).all())

    @staticmethod
    def create(db: Session, shipment: Shipment) -> Shipment:
        """
        Persists a new shipment entity into the database.
        """
        db.add(shipment)
        db.commit()
        db.refresh(shipment)
        return shipment

    @staticmethod
    def update(
        db: Session,
        shipment: Shipment,
        update_data: Dict[str, Any],
    ) -> Shipment:
        """
        Updates fields on an existing shipment entity.
        """
        for field, value in update_data.items():
            setattr(shipment, field, value)
        db.commit()
        db.refresh(shipment)
        return shipment

    @staticmethod
    def soft_delete(db: Session, shipment: Shipment) -> Shipment:
        """
        Soft-deletes a shipment by setting `is_active = False`.
        """
        shipment.is_active = False
        db.commit()
        db.refresh(shipment)
        return shipment


shipment_repository = ShipmentRepository()
