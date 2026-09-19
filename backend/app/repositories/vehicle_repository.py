"""
Vehicle Repository
==================
Encapsulates all database persistence and query operations for the Vehicle model.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.vehicle import Vehicle


class VehicleRepository:
    """
    Data access layer for Vehicle fleet records.
    """

    @staticmethod
    def get_by_id(db: Session, vehicle_id: int) -> Optional[Vehicle]:
        """
        Retrieves a vehicle by primary key ID.
        """
        return db.get(Vehicle, vehicle_id)

    @staticmethod
    def get_by_registration_number(
        db: Session,
        registration_number: str,
    ) -> Optional[Vehicle]:
        """
        Retrieves a vehicle by registration number using normalized uppercase comparison.
        """
        normalized = registration_number.strip().upper()
        stmt = select(Vehicle).where(
            func.upper(func.trim(Vehicle.registration_number)) == normalized
        )
        return db.scalars(stmt).first()

    @staticmethod
    def get_all(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> List[Vehicle]:
        """
        Retrieves a paginated list of fleet vehicles with optional status or active filtering.
        """
        stmt = select(Vehicle)

        if status:
            stmt = stmt.where(func.upper(Vehicle.status) == status.strip().upper())

        if is_active is True:
            # Active vehicles are those not decommissioned
            stmt = stmt.where(func.upper(Vehicle.status) != "DECOMMISSIONED")
        elif is_active is False:
            # Inactive vehicles are decommissioned
            stmt = stmt.where(func.upper(Vehicle.status) == "DECOMMISSIONED")

        stmt = stmt.offset(skip).limit(limit).order_by(Vehicle.id.asc())
        return list(db.scalars(stmt).all())

    @staticmethod
    def create(db: Session, vehicle: Vehicle) -> Vehicle:
        """
        Persists a new vehicle record into the database.
        """
        db.add(vehicle)
        db.commit()
        db.refresh(vehicle)
        return vehicle

    @staticmethod
    def update(
        db: Session,
        vehicle: Vehicle,
        update_data: Dict[str, Any],
    ) -> Vehicle:
        """
        Updates fields on an existing vehicle entity.
        """
        for field, value in update_data.items():
            setattr(vehicle, field, value)
        db.commit()
        db.refresh(vehicle)
        return vehicle

    @staticmethod
    def delete(db: Session, vehicle: Vehicle) -> None:
        """
        Deletes a vehicle entity from the database.
        """
        db.delete(vehicle)
        db.commit()


vehicle_repository = VehicleRepository()
