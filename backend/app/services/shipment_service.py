"""
Shipment Service
================
Business logic layer managing shipment creation, tracking numbers, lifecycle state machine,
unsafe update prevention, and relationship validation.
"""

from datetime import datetime, timezone
import uuid
from typing import List, Optional, Dict, Any, Set
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.shipment import Shipment, ShipmentStatus
from app.repositories.shipment_repository import shipment_repository
from app.repositories.warehouse_repository import warehouse_repository
from app.repositories.driver_repository import driver_repository
from app.repositories.vehicle_repository import vehicle_repository
from app.schemas.shipment import ShipmentCreate, ShipmentUpdate, ShipmentStatusUpdate

# ------------------------------------------------------------------------------
# Shipment State Machine Lifecycle Definition
# ------------------------------------------------------------------------------
# Defines valid outbound transitions from each state.
ALLOWED_TRANSITIONS: Dict[ShipmentStatus, Set[ShipmentStatus]] = {
    ShipmentStatus.CREATED: {ShipmentStatus.CONFIRMED, ShipmentStatus.CANCELLED},
    ShipmentStatus.CONFIRMED: {ShipmentStatus.ASSIGNED, ShipmentStatus.CANCELLED},
    ShipmentStatus.ASSIGNED: {ShipmentStatus.PICKED_UP, ShipmentStatus.CANCELLED},
    ShipmentStatus.PICKED_UP: {ShipmentStatus.IN_TRANSIT},
    ShipmentStatus.IN_TRANSIT: {ShipmentStatus.OUT_FOR_DELIVERY},
    ShipmentStatus.OUT_FOR_DELIVERY: {ShipmentStatus.DELIVERED, ShipmentStatus.FAILED},
    ShipmentStatus.FAILED: {ShipmentStatus.OUT_FOR_DELIVERY, ShipmentStatus.RETURNED},
    ShipmentStatus.DELIVERED: set(),  # Terminal state
    ShipmentStatus.CANCELLED: set(),  # Terminal state
    ShipmentStatus.RETURNED: set(),   # Terminal state
}


def generate_unique_tracking_number() -> str:
    """
    Generates a unique human-readable tracking identifier in the format:
    FG-YYYYMMDD-XXXXXXXX
    """
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    unique_suffix = uuid.uuid4().hex[:8].upper()
    return f"FG-{date_str}-{unique_suffix}"


class ShipmentService:
    """
    Business service managing shipments and lifecycle transitions.
    """

    def __init__(
        self,
        repository=shipment_repository,
        warehouse_repo=warehouse_repository,
        driver_repo=driver_repository,
        vehicle_repo=vehicle_repository,
    ):
        self.repository = repository
        self.warehouse_repo = warehouse_repo
        self.driver_repo = driver_repo
        self.vehicle_repo = vehicle_repo

    def create_shipment(
        self,
        db: Session,
        payload: ShipmentCreate,
    ) -> Shipment:
        """
        Validates relationships, assigns a unique tracking number, and registers a shipment.
        """
        # 1. Validate or generate unique tracking number
        if payload.tracking_number:
            normalized_tracking = payload.tracking_number.strip().upper()
            existing = self.repository.get_by_tracking_number(db, normalized_tracking)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Tracking number '{normalized_tracking}' is already registered",
                )
        else:
            # Generate collision-free tracking number
            while True:
                candidate = generate_unique_tracking_number()
                if not self.repository.get_by_tracking_number(db, candidate):
                    normalized_tracking = candidate
                    break

        # 2. Validate Origin Warehouse if provided
        if payload.origin_warehouse_id is not None:
            wh = self.warehouse_repo.get_by_id(db, payload.origin_warehouse_id)
            if not wh:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Warehouse with ID {payload.origin_warehouse_id} does not exist",
                )
            if not wh.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Warehouse '{wh.name}' (ID {payload.origin_warehouse_id}) is inactive",
                )

        # 3. Validate Driver if assigned
        if payload.assigned_driver_id is not None:
            drv = self.driver_repo.get_by_id(db, payload.assigned_driver_id)
            if not drv:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Driver with ID {payload.assigned_driver_id} does not exist",
                )

        # 4. Validate Vehicle if assigned
        if payload.assigned_vehicle_id is not None:
            veh = self.vehicle_repo.get_by_id(db, payload.assigned_vehicle_id)
            if not veh:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Vehicle with ID {payload.assigned_vehicle_id} does not exist",
                )

        shipment = Shipment(
            tracking_number=normalized_tracking,
            origin_warehouse_id=payload.origin_warehouse_id,
            destination_address=payload.destination_address.strip(),
            destination_city=payload.destination_city.strip(),
            destination_state=payload.destination_state.strip(),
            destination_postal_code=payload.destination_postal_code.strip(),
            status=ShipmentStatus.CREATED,
            assigned_driver_id=payload.assigned_driver_id,
            assigned_vehicle_id=payload.assigned_vehicle_id,
            total_weight_kg=payload.total_weight_kg,
            total_volume_cbm=payload.total_volume_cbm,
            scheduled_pickup_at=payload.scheduled_pickup_at,
            is_active=True,
        )
        return self.repository.create(db, shipment)

    def get_shipment(self, db: Session, shipment_id: int) -> Shipment:
        """
        Retrieves a shipment by primary key ID or raises HTTP 404.
        """
        shipment = self.repository.get_by_id(db, shipment_id)
        if not shipment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Shipment with ID {shipment_id} was not found",
            )
        return shipment

    def get_shipment_by_tracking(self, db: Session, tracking_number: str) -> Shipment:
        """
        Retrieves a shipment by tracking number or raises HTTP 404.
        """
        shipment = self.repository.get_by_tracking_number(db, tracking_number)
        if not shipment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Shipment with tracking number '{tracking_number}' was not found",
            )
        return shipment

    def list_shipments(
        self,
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
        return self.repository.get_all(
            db,
            skip=skip,
            limit=limit,
            status=status,
            tracking_number=tracking_number,
            origin_warehouse_id=origin_warehouse_id,
            is_active=is_active,
        )

    def update_shipment(
        self,
        db: Session,
        shipment_id: int,
        payload: ShipmentUpdate,
    ) -> Shipment:
        """
        Updates permitted shipment information. Prevents unsafe updates after delivery
        or in terminal states.
        """
        shipment = self.get_shipment(db, shipment_id)

        # Disallow updating delivered or cancelled shipments
        if shipment.status == ShipmentStatus.DELIVERED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot modify shipment details after successful delivery",
            )
        if shipment.status in (ShipmentStatus.CANCELLED, ShipmentStatus.RETURNED):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot modify shipment in terminal state '{shipment.status.value}'",
            )

        update_data = payload.model_dump(exclude_unset=True)

        # Validate warehouse if changed
        if "origin_warehouse_id" in update_data and update_data["origin_warehouse_id"] is not None:
            wh = self.warehouse_repo.get_by_id(db, update_data["origin_warehouse_id"])
            if not wh or not wh.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Warehouse with ID {update_data['origin_warehouse_id']} does not exist or is inactive",
                )

        # Validate driver if changed
        if "assigned_driver_id" in update_data and update_data["assigned_driver_id"] is not None:
            drv = self.driver_repo.get_by_id(db, update_data["assigned_driver_id"])
            if not drv:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Driver with ID {update_data['assigned_driver_id']} does not exist",
                )

        # Validate vehicle if changed
        if "assigned_vehicle_id" in update_data and update_data["assigned_vehicle_id"] is not None:
            veh = self.vehicle_repo.get_by_id(db, update_data["assigned_vehicle_id"])
            if not veh:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Vehicle with ID {update_data['assigned_vehicle_id']} does not exist",
                )

        # Strip strings
        for field in ("destination_address", "destination_city", "destination_state", "destination_postal_code"):
            if field in update_data and update_data[field] is not None:
                update_data[field] = update_data[field].strip()

        if update_data:
            return self.repository.update(db, shipment, update_data)
        return shipment

    def update_shipment_status(
        self,
        db: Session,
        shipment_id: int,
        payload: ShipmentStatusUpdate,
    ) -> Shipment:
        """
        Enforces state machine transitions and updates the shipment status.
        """
        shipment = self.get_shipment(db, shipment_id)
        current_status = shipment.status
        target_status = payload.status

        # If already in the target status, return cleanly
        if current_status == target_status:
            return shipment

        allowed_next = ALLOWED_TRANSITIONS.get(current_status, set())
        if target_status not in allowed_next:
            allowed_names = [s.value for s in allowed_next] or ["None (Terminal State)"]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Illegal status transition from '{current_status.value}' to '{target_status.value}'. "
                    f"Permitted transitions: {', '.join(allowed_names)}"
                ),
            )

        update_dict: Dict[str, Any] = {"status": target_status}

        # If transitioning to DELIVERED, record timestamp
        if target_status == ShipmentStatus.DELIVERED:
            update_dict["delivered_at"] = datetime.now(timezone.utc)

        return self.repository.update(db, shipment, update_dict)

    def delete_shipment(self, db: Session, shipment_id: int) -> Shipment:
        """
        Soft-deletes a shipment by setting `is_active = False` to preserve historical audit trail.
        Raises HTTP 404 if not found.
        """
        shipment = self.get_shipment(db, shipment_id)
        return self.repository.soft_delete(db, shipment)


shipment_service = ShipmentService()
