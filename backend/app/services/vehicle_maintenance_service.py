"""Business rules for vehicle maintenance schedules and history."""

from typing import List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.vehicle import Vehicle
from app.models.vehicle_maintenance import VehicleMaintenance
from app.schemas.vehicle_maintenance import VehicleMaintenanceCreate, VehicleMaintenanceUpdate


class VehicleMaintenanceService:
    def _get_vehicle(self, db: Session, vehicle_id: int) -> Vehicle:
        vehicle = db.get(Vehicle, vehicle_id)
        if vehicle is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
        return vehicle

    def list_records(self, db: Session, vehicle_id: int) -> List[VehicleMaintenance]:
        self._get_vehicle(db, vehicle_id)
        return (
            db.query(VehicleMaintenance)
            .filter(VehicleMaintenance.vehicle_id == vehicle_id)
            .order_by(VehicleMaintenance.scheduled_date.desc(), VehicleMaintenance.id.desc())
            .all()
        )

    def create_record(
        self, db: Session, vehicle_id: int, payload: VehicleMaintenanceCreate
    ) -> VehicleMaintenance:
        vehicle = self._get_vehicle(db, vehicle_id)
        if vehicle.status == "DECOMMISSIONED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot schedule maintenance for a decommissioned vehicle",
            )
        record = VehicleMaintenance(vehicle_id=vehicle_id, **payload.model_dump())
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    def update_record(
        self, db: Session, record_id: int, payload: VehicleMaintenanceUpdate
    ) -> VehicleMaintenance:
        record = db.get(VehicleMaintenance, record_id)
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Maintenance record not found")
        values = payload.model_dump(exclude_unset=True)
        for field, value in values.items():
            setattr(record, field, value)
        if record.status == "COMPLETED" and record.completed_at is None:
            from datetime import datetime, timezone
            record.completed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(record)
        return record


vehicle_maintenance_service = VehicleMaintenanceService()
