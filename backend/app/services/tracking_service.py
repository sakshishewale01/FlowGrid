"""
Tracking Service
================
Business logic service managing shipment status audit histories,
milestone event recordings, and aggregated real-time tracking views.
"""

from datetime import datetime, timezone
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.shipment import Shipment
from app.models.tracking import ShipmentStatusHistory, ShipmentTrackingEvent
from app.models.user import User
from app.repositories.shipment_repository import shipment_repository
from app.repositories.tracking_repository import tracking_repository
from app.schemas.tracking import (
    ShipmentTrackingEventCreate,
    LatestTrackingInfoResponse,
    ShipmentStatusHistoryResponse,
    ShipmentTrackingEventResponse,
)


class TrackingService:
    """
    Business service managing tracking histories and checkpoint events.
    """

    def __init__(
        self,
        shipment_repo=shipment_repository,
        tracking_repo=tracking_repository,
    ):
        self.shipment_repo = shipment_repo
        self.tracking_repo = tracking_repo

    def _verify_shipment_exists(self, db: Session, shipment_id: int) -> Shipment:
        """
        Validates shipment existence or raises 404 Not Found.
        """
        shipment = self.shipment_repo.get_by_id(db, shipment_id)
        if not shipment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Shipment with ID {shipment_id} was not found",
            )
        return shipment

    def get_status_history(
        self,
        db: Session,
        shipment_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ShipmentStatusHistory]:
        """
        Returns the persistent state transition audit trail for a shipment, newest first.
        """
        self._verify_shipment_exists(db, shipment_id)
        return self.tracking_repo.get_status_history_by_shipment(
            db, shipment_id, skip=skip, limit=limit
        )

    def add_tracking_event(
        self,
        db: Session,
        shipment_id: int,
        payload: ShipmentTrackingEventCreate,
        current_user: Optional[User] = None,
    ) -> ShipmentTrackingEvent:
        """
        Appends a physical checkpoint or transit milestone to a shipment.
        Accessible to ADMIN and MANAGER roles.
        """
        self._verify_shipment_exists(db, shipment_id)

        event_time = payload.timestamp or datetime.now(timezone.utc)
        event = ShipmentTrackingEvent(
            shipment_id=shipment_id,
            event_type=payload.event_type.strip().upper(),
            location=payload.location.strip(),
            description=payload.description.strip(),
            timestamp=event_time,
            created_by_user_id=current_user.id if current_user else None,
        )
        return self.tracking_repo.create_tracking_event(db, event)

    def get_tracking_events(
        self,
        db: Session,
        shipment_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ShipmentTrackingEvent]:
        """
        Returns chronological physical tracking events for a shipment, newest first.
        """
        self._verify_shipment_exists(db, shipment_id)
        return self.tracking_repo.get_tracking_events_by_shipment(
            db, shipment_id, skip=skip, limit=limit
        )

    def get_latest_tracking_info(
        self,
        db: Session,
        shipment_id: int,
    ) -> LatestTrackingInfoResponse:
        """
        Aggregates the current operational state, most recent status transition,
        and latest physical tracking event for a shipment.
        """
        shipment = self._verify_shipment_exists(db, shipment_id)

        latest_history = self.tracking_repo.get_latest_status_history(db, shipment_id)
        latest_event = self.tracking_repo.get_latest_tracking_event(db, shipment_id)

        history_response = (
            ShipmentStatusHistoryResponse.model_validate(latest_history)
            if latest_history
            else None
        )
        event_response = (
            ShipmentTrackingEventResponse.model_validate(latest_event)
            if latest_event
            else None
        )

        return LatestTrackingInfoResponse(
            shipment_id=shipment.id,
            tracking_number=shipment.tracking_number,
            current_status=shipment.status,
            destination_city=shipment.destination_city,
            destination_state=shipment.destination_state,
            delivered_at=shipment.delivered_at,
            latest_status_history=history_response,
            latest_tracking_event=event_response,
        )


tracking_service = TrackingService()
