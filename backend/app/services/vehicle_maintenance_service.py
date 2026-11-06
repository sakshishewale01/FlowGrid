"""Business rules for vehicle maintenance schedules and history."""

from datetime import date, timedelta
from typing import List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.vehicle import Vehicle
from app.models.vehicle_maintenance import VehicleMaintenance
from app.schemas.vehicle_maintenance import VehicleMaintenanceCreate, VehicleMaintenanceUpdate
from app.repositories.vehicle_maintenance_repository import vehicle_maintenance_repository


class VehicleMaintenanceService:
    def _get_vehicle(self, db: Session, vehicle_id: int) -> Vehicle:
        vehicle = db.get(Vehicle, vehicle_id)
        if vehicle is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
        return vehicle

    def list_records(self, db: Session, vehicle_id: int) -> List[VehicleMaintenance]:
        self._get_vehicle(db, vehicle_id)
        return vehicle_maintenance_repository.list_for_vehicle(db, vehicle_id)

    def list_due(self, db: Session, days: int) -> List[tuple[VehicleMaintenance, Vehicle, date, str]]:
        today = date.today()
        records = vehicle_maintenance_repository.list_due(db, today, today + timedelta(days=days))
        result = []
        for record in records:
            vehicle = self._get_vehicle(db, record.vehicle_id)
            due_date = record.next_service_due_date or record.scheduled_date
            due_status = "OVERDUE" if due_date < today else "UPCOMING"
            result.append((record, vehicle, due_date, due_status))
        return result

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
        return vehicle_maintenance_repository.create(db, record)

    def update_record(
        self, db: Session, record_id: int, payload: VehicleMaintenanceUpdate
    ) -> VehicleMaintenance:
        record = vehicle_maintenance_repository.get_by_id(db, record_id)
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Maintenance record not found")
        values = payload.model_dump(exclude_unset=True)
        if values.get("status") == "COMPLETED" and record.completed_at is None:
            from datetime import datetime, timezone
            record.completed_at = datetime.now(timezone.utc)
        return vehicle_maintenance_repository.update(db, record, values)


vehicle_maintenance_service = VehicleMaintenanceService()
