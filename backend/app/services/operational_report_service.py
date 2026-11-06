"""CSV operational reports with spreadsheet formula injection protection."""

import csv
import io
from datetime import date
from typing import Iterable, List

from sqlalchemy.orm import Session

from app.models.inventory import Inventory
from app.models.shipment import Shipment
from app.models.vehicle import Vehicle


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
    def build(self, db: Session, report_type: str, start_date: date | None, end_date: date | None) -> str:
        if report_type == "shipments":
            query = db.query(Shipment).order_by(Shipment.created_at.asc())
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
        if report_type == "inventory":
            records = db.query(Inventory).order_by(Inventory.id.asc()).all()
            return _csv_content(
                ["inventory_id", "warehouse_id", "product_id", "quantity", "reorder_level", "updated_at"],
                ((item.id, item.warehouse_id, item.product_id, item.quantity, item.reorder_level, item.updated_at) for item in records),
            )
        vehicles = db.query(Vehicle).order_by(Vehicle.id.asc()).all()
        return _csv_content(
            ["vehicle_id", "registration_number", "vehicle_type", "capacity", "status", "created_at", "updated_at"],
            ((item.id, item.registration_number, item.vehicle_type, item.capacity, item.status, item.created_at, item.updated_at) for item in vehicles),
        )


operational_report_service = OperationalReportService()
