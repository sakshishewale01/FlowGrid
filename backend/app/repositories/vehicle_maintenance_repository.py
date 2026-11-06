"""Persistence operations for vehicle maintenance records."""

from datetime import date
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.vehicle_maintenance import VehicleMaintenance


class VehicleMaintenanceRepository:
    @staticmethod
    def get_by_id(db: Session, record_id: int) -> Optional[VehicleMaintenance]:
        return db.get(VehicleMaintenance, record_id)

    @staticmethod
    def list_for_vehicle(db: Session, vehicle_id: int) -> List[VehicleMaintenance]:
        statement = (
            select(VehicleMaintenance)
            .where(VehicleMaintenance.vehicle_id == vehicle_id)
            .order_by(VehicleMaintenance.scheduled_date.desc(), VehicleMaintenance.id.desc())
        )
        return list(db.scalars(statement).all())

    @staticmethod
    def list_due(
        db: Session,
        start_date: date,
        end_date: date,
    ) -> List[VehicleMaintenance]:
        statement = (
            select(VehicleMaintenance)
            .where(
                VehicleMaintenance.status.not_in(("COMPLETED", "CANCELLED")),
                func.coalesce(
                    VehicleMaintenance.next_service_due_date,
                    VehicleMaintenance.scheduled_date,
                ).between(start_date, end_date)
                | (
                    func.coalesce(
                        VehicleMaintenance.next_service_due_date,
                        VehicleMaintenance.scheduled_date,
                    )
                    < start_date
                ),
            )
            .order_by(VehicleMaintenance.scheduled_date.asc(), VehicleMaintenance.id.asc())
        )
        return list(db.scalars(statement).all())

    @staticmethod
    def create(db: Session, record: VehicleMaintenance) -> VehicleMaintenance:
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def update(db: Session, record: VehicleMaintenance, values: dict) -> VehicleMaintenance:
        for field, value in values.items():
            setattr(record, field, value)
        db.commit()
        db.refresh(record)
        return record


vehicle_maintenance_repository = VehicleMaintenanceRepository()
