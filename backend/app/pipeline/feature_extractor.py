"""
FlowGrid - AI Pipeline Feature Extractor
========================================
Extracts operational entities and milestone timestamps from PostgreSQL/SQLite
tables without modifying underlying operational states.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload

from app.models.shipment import Shipment, ShipmentStatus
from app.models.warehouse import Warehouse
from app.models.driver import Driver
from app.models.vehicle import Vehicle
from app.models.route import Route, RouteShipment
from app.models.tracking import ShipmentStatusHistory


@dataclass
class ExtractedShipmentContext:
    """
    Consolidated operational context extracted for a single shipment.
    """
    shipment: Shipment
    warehouse: Optional[Warehouse]
    driver: Optional[Driver]
    vehicle: Optional[Vehicle]
    route: Optional[Route]
    status_history: List[ShipmentStatusHistory]
    actual_pickup_at: Optional[datetime]
    actual_delivered_at: Optional[datetime]
    delay_signals_count: int


class FeatureExtractor:
    """
    Orchestrates querying operational tables to collect raw features for ML processing.
    """

    @staticmethod
    def extract_single_shipment(db: Session, shipment_id: int) -> Optional[ExtractedShipmentContext]:
        """
        Extracts full operational context for a single shipment by ID.
        """
        shipment = (
            db.query(Shipment)
            .options(
                joinedload(Shipment.origin_warehouse),
                joinedload(Shipment.assigned_driver).joinedload(Driver.user),
                joinedload(Shipment.assigned_vehicle),
                joinedload(Shipment.routes),
                joinedload(Shipment.status_history),
            )
            .filter(Shipment.id == shipment_id)
            .first()
        )
        if not shipment:
            return None
        return FeatureExtractor._build_context(shipment)

    @staticmethod
    def extract_all_shipments(
        db: Session,
        include_undelivered: bool = True,
        limit: Optional[int] = None,
    ) -> List[ExtractedShipmentContext]:
        """
        Extracts operational context for all active shipments.
        """
        query = (
            db.query(Shipment)
            .options(
                joinedload(Shipment.origin_warehouse),
                joinedload(Shipment.assigned_driver).joinedload(Driver.user),
                joinedload(Shipment.assigned_vehicle),
                joinedload(Shipment.routes),
                joinedload(Shipment.status_history),
            )
            .filter(Shipment.is_active.is_(True))
            .order_by(Shipment.created_at.asc())
        )

        if not include_undelivered:
            query = query.filter(Shipment.status == ShipmentStatus.DELIVERED)

        if limit is not None and limit > 0:
            query = query.limit(limit)

        shipments = query.all()
        return [FeatureExtractor._build_context(s) for s in shipments]

    @staticmethod
    def _build_context(shipment: Shipment) -> ExtractedShipmentContext:
        """
        Parses history and associated relations into a consolidated context object.
        """
        warehouse = shipment.origin_warehouse
        driver = shipment.assigned_driver
        vehicle = shipment.assigned_vehicle
        route = shipment.routes[0] if shipment.routes else None

        # Sort status history chronologically (ascending)
        history = sorted(
            shipment.status_history or [],
            key=lambda h: h.created_at or datetime.min,
        )

        # Detect actual pickup timestamp (first transition to PICKED_UP or IN_TRANSIT)
        actual_pickup_at: Optional[datetime] = None
        for h in history:
            if h.new_status in (ShipmentStatus.PICKED_UP, ShipmentStatus.IN_TRANSIT):
                actual_pickup_at = h.created_at
                break

        # Fallback to scheduled pickup if status history milestone not recorded
        if actual_pickup_at is None and shipment.scheduled_pickup_at is not None:
            actual_pickup_at = shipment.scheduled_pickup_at

        # Detect actual delivery timestamp
        actual_delivered_at: Optional[datetime] = shipment.delivered_at
        if actual_delivered_at is None:
            for h in history:
                if h.new_status == ShipmentStatus.DELIVERED:
                    actual_delivered_at = h.created_at
                    break

        # Count historical delay signals prior to or during dispatch
        delay_signals_count = 0
        for h in history:
            if h.new_status == ShipmentStatus.FAILED:
                delay_signals_count += 1
            elif h.remarks and any(k in h.remarks.lower() for k in ("delay", "late", "breakdown", "traffic", "reroute")):
                delay_signals_count += 1

        return ExtractedShipmentContext(
            shipment=shipment,
            warehouse=warehouse,
            driver=driver,
            vehicle=vehicle,
            route=route,
            status_history=history,
            actual_pickup_at=actual_pickup_at,
            actual_delivered_at=actual_delivered_at,
            delay_signals_count=delay_signals_count,
        )


feature_extractor = FeatureExtractor()
