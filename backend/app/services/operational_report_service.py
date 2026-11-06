"""CSV operational reports with spreadsheet formula injection protection."""

import csv
import io
from datetime import date, datetime, timezone
from typing import Iterable, List

from sqlalchemy.orm import Session, joinedload

from app.models.inventory import Inventory
from app.models.shipment import Shipment
from app.models.vehicle import Vehicle
from app.models.route import Route
from app.models.tracking import ShipmentStatusHistory


def _safe_cell(value: object) -> str:
    text = "" if value is None else str(value)
    if text.startswith(("=", "+", "-", "@")):
        return "'" + text
    return text


def _csv_content(headers: List[str], rows: Iterable[Iterable[object]]) -> str:
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(headers)
    for row in rows:
        writer.writerow([_safe_cell(value) for value in row])
    return output.getvalue()


class OperationalReportService:
    @staticmethod
    def _in_range(value: datetime | None, start_date: date | None, end_date: date | None) -> bool:
        if value is None:
            return False
        value_date = value.date()
        return (start_date is None or value_date >= start_date) and (end_date is None or value_date <= end_date)

    @staticmethod
    def _delivery_metrics(item: Shipment) -> tuple[str | None, float | None, float | None, str | None]:
        delivered_at = item.delivered_at
        if delivered_at is None:
            delivered_history = [
                event for event in item.status_history
                if event.new_status.value == "DELIVERED"
            ]
            delivered_at = min((event.created_at for event in delivered_history), default=None)
        pickup_history = [
            event for event in item.status_history
            if event.new_status.value in {"PICKED_UP", "IN_TRANSIT"}
        ]
        pickup_at = min((event.created_at for event in pickup_history), default=item.scheduled_pickup_at)
        duration = None
        if pickup_at and delivered_at and delivered_at >= pickup_at:
            duration = round((delivered_at - pickup_at).total_seconds() / 3600, 2)
        route_duration = None
        if item.routes:
            route_duration = next(
                (float(route.estimated_duration) for route in item.routes if route.estimated_duration is not None),
                None,
            )
        on_time = None
        if duration is not None and route_duration is not None:
            on_time = "true" if duration <= route_duration + 0.1 else "false"
        return delivered_at.isoformat() if delivered_at else None, duration, route_duration, on_time

    def build(self, db: Session, report_type: str, start_date: date | None, end_date: date | None) -> str:
        if report_type == "shipments":
            query = db.query(Shipment).options(joinedload(Shipment.status_history), joinedload(Shipment.routes)).order_by(Shipment.created_at.asc())
            if start_date:
                query = query.filter(Shipment.created_at >= start_date)
            if end_date:
                query = query.filter(Shipment.created_at < end_date.fromordinal(end_date.toordinal() + 1))
            shipments = query.all()
            return _csv_content(
                ["shipment_id", "tracking_number", "status", "destination_city", "destination_state", "created_at", "delivered_at", "total_weight_kg"],
                (
                    (
                        item.id, item.tracking_number, item.status.value if hasattr(item.status, "value") else item.status,
                        item.destination_city, item.destination_state, item.created_at, item.delivered_at,
                        item.total_weight_kg,
                    )
                    for item in shipments
                ),
            )
        if report_type == "delivery":
            query = db.query(Shipment).options(joinedload(Shipment.status_history), joinedload(Shipment.routes)).filter(Shipment.status == "DELIVERED").order_by(Shipment.id.asc())
            records = query.all()
            rows = []
            for item in records:
                delivered_at, duration, planned_duration, on_time = self._delivery_metrics(item)
                if delivered_at and self._in_range(datetime.fromisoformat(delivered_at), start_date, end_date):
                    rows.append((item.id, item.tracking_number, delivered_at, duration, planned_duration, on_time))
            return _csv_content(
                ["shipment_id", "tracking_number", "delivered_at", "actual_duration_hours", "planned_duration_hours", "on_time"],
                rows,
            )
        if report_type == "inventory":
            records = db.query(Inventory).order_by(Inventory.id.asc()).all()
            records = [item for item in records if self._in_range(item.updated_at, start_date, end_date)]
            return _csv_content(
                ["inventory_id", "warehouse_id", "product_id", "quantity", "reorder_level", "updated_at"],
                ((item.id, item.warehouse_id, item.product_id, item.quantity, item.reorder_level, item.updated_at) for item in records),
            )
        if report_type == "fleet":
            vehicles = db.query(Vehicle).order_by(Vehicle.id.asc()).all()
            rows = []
            for vehicle in vehicles:
                assignments = [
                    shipment for shipment in db.query(Shipment).filter(
                        Shipment.assigned_vehicle_id == vehicle.id
                    ).all()
                    if self._in_range(shipment.updated_at, start_date, end_date)
                ]
                rows.append((
                    vehicle.id,
                    vehicle.registration_number,
                    vehicle.vehicle_type,
                    vehicle.capacity,
                    vehicle.status,
                    len(assignments),
                    sum(float(item.total_weight_kg or 0) for item in assignments),
                    vehicle.created_at,
                    vehicle.updated_at,
                ))
            return _csv_content(
                ["vehicle_id", "registration_number", "vehicle_type", "capacity", "status", "assigned_shipments", "assigned_weight_kg", "created_at", "updated_at"],
                rows,
            )
        vehicles = db.query(Vehicle).order_by(Vehicle.id.asc()).all()
        return _csv_content(
            ["vehicle_id", "registration_number", "vehicle_type", "capacity", "status", "created_at", "updated_at"],
            ((item.id, item.registration_number, item.vehicle_type, item.capacity, item.status, item.created_at, item.updated_at) for item in vehicles),
        )


operational_report_service = OperationalReportService()
