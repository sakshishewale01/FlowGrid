"""
Vehicle Service
===============
Business logic layer managing fleet vehicle registrations, unique registration
number enforcement, carrying capacity validations, and repository calls.
"""

from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.vehicle import Vehicle
from app.models.shipment import Shipment, ShipmentStatus
from app.repositories.vehicle_repository import vehicle_repository
from app.schemas.vehicle import VehicleCreate, VehicleUpdate


class VehicleService:
    """
    Business service for vehicle fleet management.
    """

    def __init__(self, repository=vehicle_repository):
        self.repository = repository

    def create_vehicle(self, db: Session, payload: VehicleCreate) -> Vehicle:
        """
        Validates unique registration number and capacity before creating a vehicle record.
        """
        normalized_reg = payload.registration_number.strip().upper()

        # Check for duplicate registration number
        conflict = self.repository.get_by_registration_number(db, normalized_reg)
        if conflict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A vehicle with registration number '{normalized_reg}' already exists",
            )

        vehicle = Vehicle(
            registration_number=normalized_reg,
            vehicle_type=payload.vehicle_type.strip(),
            capacity=payload.capacity,
            status=payload.status.strip().upper(),
        )
        return self.repository.create(db, vehicle)

    def get_vehicle(self, db: Session, vehicle_id: int) -> Vehicle:
        """
        Retrieves a vehicle by primary key ID or raises HTTP 404 if not found.
        """
        vehicle = self.repository.get_by_id(db, vehicle_id)
        if not vehicle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vehicle with ID {vehicle_id} was not found",
            )
        return vehicle

    def list_vehicles(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> List[Vehicle]:
        """
        Retrieves a paginated list of vehicles with optional status or active filtering.
        """
        return self.repository.get_all(
            db,
            skip=skip,
            limit=limit,
            status=status,
            is_active=is_active,
        )

    def update_vehicle(
        self,
        db: Session,
        vehicle_id: int,
        payload: VehicleUpdate,
    ) -> Vehicle:
        """
        Updates an existing vehicle record, validating registration uniqueness if altered.
        Raises HTTP 404 if not found.
        """
        vehicle = self.get_vehicle(db, vehicle_id)

        update_data = payload.model_dump(exclude_unset=True)

        if "registration_number" in update_data and update_data["registration_number"] is not None:
            new_reg = update_data["registration_number"].strip().upper()
            if new_reg != vehicle.registration_number.strip().upper():
                conflict = self.repository.get_by_registration_number(db, new_reg)
                if conflict and conflict.id != vehicle_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"A vehicle with registration number '{new_reg}' already exists",
                    )
            update_data["registration_number"] = new_reg

        if "vehicle_type" in update_data and update_data["vehicle_type"] is not None:
            update_data["vehicle_type"] = update_data["vehicle_type"].strip()

        if "status" in update_data and update_data["status"] is not None:
            new_status = update_data["status"].strip().upper()
            if new_status in ("MAINTENANCE", "DECOMMISSIONED") and vehicle.status not in ("MAINTENANCE", "DECOMMISSIONED"):
                active_shipments_count = db.query(Shipment).filter(
                    Shipment.assigned_vehicle_id == vehicle_id,
                    Shipment.status.in_([
                        ShipmentStatus.CREATED,
                        ShipmentStatus.CONFIRMED,
                        ShipmentStatus.ASSIGNED,
                        ShipmentStatus.PICKED_UP,
                        ShipmentStatus.IN_TRANSIT,
                        ShipmentStatus.OUT_FOR_DELIVERY,
                    ]),
                ).count()
                if active_shipments_count > 0:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Cannot change vehicle status to {new_status} while assigned to {active_shipments_count} active shipment(s)",
                    )
            update_data["status"] = new_status

        if update_data:
            return self.repository.update(db, vehicle, update_data)
        return vehicle

    def delete_vehicle(self, db: Session, vehicle_id: int) -> Dict[str, Any]:
        """
        Deletes a vehicle record from the database.
        Raises HTTP 404 if not found.
        """
        vehicle = self.get_vehicle(db, vehicle_id)
        active_shipments_count = db.query(Shipment).filter(
            Shipment.assigned_vehicle_id == vehicle_id,
            Shipment.status.in_([
                ShipmentStatus.CREATED,
                ShipmentStatus.CONFIRMED,
                ShipmentStatus.ASSIGNED,
                ShipmentStatus.PICKED_UP,
                ShipmentStatus.IN_TRANSIT,
                ShipmentStatus.OUT_FOR_DELIVERY,
            ]),
        ).count()
        if active_shipments_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete vehicle with ID {vehicle_id} while assigned to {active_shipments_count} active shipment(s)",
            )
        self.repository.delete(db, vehicle)
        return {
            "message": f"Vehicle with ID {vehicle_id} was deleted successfully",
            "id": vehicle_id,
        }


vehicle_service = VehicleService()
