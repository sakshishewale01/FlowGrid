"""
Tracking Repository
===================
Data access layer for shipment lifecycle status audit trails and physical tracking events.
"""

from typing import List, Optional
from sqlalchemy import select, desc
from sqlalchemy.orm import Session, joinedload

from app.models.tracking import ShipmentStatusHistory, ShipmentTrackingEvent


class TrackingRepository:
    """
    Encapsulates database queries for status history and physical tracking events.
    """

    # --------------------------------------------------------------------------
    # Status History Operations
    # --------------------------------------------------------------------------
    def create_status_history(
        self,
        db: Session,
        history: ShipmentStatusHistory,
    ) -> ShipmentStatusHistory:
        """
        Persists a new status history record within the current transaction session.
        """
        db.add(history)
        db.commit()
        db.refresh(history)
        return history

    def get_status_history_by_shipment(
        self,
        db: Session,
        shipment_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ShipmentStatusHistory]:
        """
        Retrieves status transitions for a shipment, ordered from newest to oldest.
        """
        stmt = (
            select(ShipmentStatusHistory)
            .options(joinedload(ShipmentStatusHistory.changed_by))
            .where(ShipmentStatusHistory.shipment_id == shipment_id)
            .order_by(
                desc(ShipmentStatusHistory.created_at),
                desc(ShipmentStatusHistory.id),
            )
            .offset(skip)
            .limit(limit)
        )
        return list(db.scalars(stmt).all())

    def get_latest_status_history(
        self,
        db: Session,
        shipment_id: int,
    ) -> Optional[ShipmentStatusHistory]:
        """
        Retrieves the most recent status transition record for a shipment.
        """
        stmt = (
            select(ShipmentStatusHistory)
            .options(joinedload(ShipmentStatusHistory.changed_by))
            .where(ShipmentStatusHistory.shipment_id == shipment_id)
            .order_by(
                desc(ShipmentStatusHistory.created_at),
                desc(ShipmentStatusHistory.id),
            )
            .limit(1)
        )
        return db.scalars(stmt).first()

    # --------------------------------------------------------------------------
    # Tracking Event Operations
    # --------------------------------------------------------------------------
    def create_tracking_event(
        self,
        db: Session,
        event: ShipmentTrackingEvent,
    ) -> ShipmentTrackingEvent:
        """
        Persists a physical tracking milestone event.
        """
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    def get_tracking_events_by_shipment(
        self,
        db: Session,
        shipment_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ShipmentTrackingEvent]:
        """
        Retrieves physical tracking events for a shipment, ordered from newest to oldest.
        """
        stmt = (
            select(ShipmentTrackingEvent)
            .options(joinedload(ShipmentTrackingEvent.created_by))
            .where(ShipmentTrackingEvent.shipment_id == shipment_id)
            .order_by(
                desc(ShipmentTrackingEvent.timestamp),
                desc(ShipmentTrackingEvent.id),
            )
            .offset(skip)
            .limit(limit)
        )
        return list(db.scalars(stmt).all())

    def get_latest_tracking_event(
        self,
        db: Session,
        shipment_id: int,
    ) -> Optional[ShipmentTrackingEvent]:
        """
        Retrieves the latest physical tracking event for a shipment.
        """
        stmt = (
            select(ShipmentTrackingEvent)
            .options(joinedload(ShipmentTrackingEvent.created_by))
            .where(ShipmentTrackingEvent.shipment_id == shipment_id)
            .order_by(
                desc(ShipmentTrackingEvent.timestamp),
                desc(ShipmentTrackingEvent.id),
            )
            .limit(1)
        )
        return db.scalars(stmt).first()


tracking_repository = TrackingRepository()
