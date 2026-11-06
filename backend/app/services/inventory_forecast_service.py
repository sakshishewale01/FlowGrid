"""Transparent inventory trends and demand planning grounded in movement history."""

from datetime import datetime, timedelta, timezone
from math import ceil
from typing import List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.inventory import Inventory
from app.repositories.inventory_movement_repository import inventory_movement_repository
from app.schemas.inventory_forecast import InventoryForecastResponse, InventoryRecommendationResponse


class InventoryForecastService:
    MIN_MOVEMENTS_FOR_FORECAST = 3

    def _calculate(self, db: Session, record: Inventory, horizon_days: int):
        since = datetime.now(timezone.utc) - timedelta(days=90)
        movements = inventory_movement_repository.list_for_inventory(db, record.id, since)
        outbound_units = sum(max(0, -movement.quantity_delta) for movement in movements)
        average_daily_demand = outbound_units / 90
        sufficient = len(movements) >= self.MIN_MOVEMENTS_FOR_FORECAST and outbound_units > 0
        projected = max(0.0, record.quantity - average_daily_demand * horizon_days) if sufficient else float(record.reorder_level)
        stockout_days = (
            record.quantity / average_daily_demand
            if sufficient and average_daily_demand > 0
            else None
        )
        reorder = record.quantity <= record.reorder_level or (
            stockout_days is not None and stockout_days <= horizon_days
        )
        explanation = [
            f"Analyzed {len(movements)} recorded inventory movements from the last 90 days.",
        ]
        limitations = [
            "The estimate uses recorded negative quantity movements as demand; receipts and unrecorded demand are not inferred.",
            "No model accuracy is claimed; this is a simple average-rate estimate.",
        ]
        if sufficient:
            explanation.append(f"Average recorded outbound demand is {average_daily_demand:.2f} units per day.")
            data_sufficiency = "sufficient"
        else:
            explanation.append("Insufficient recorded outbound history for a demand estimate; the reorder threshold is used as the planning baseline.")
            limitations.append("At least three recorded movements with outbound demand are required for this estimate.")
            data_sufficiency = "insufficient"
        return {
            "inventory_id": record.id,
            "product_id": record.product_id,
            "warehouse_id": record.warehouse_id,
            "horizon_days": horizon_days,
            "forecast_quantity": round(projected, 2),
            "current_quantity": record.quantity,
            "reorder_level": record.reorder_level,
            "reorder_recommended": reorder,
            "data_sufficiency": data_sufficiency,
            "average_daily_demand": round(average_daily_demand, 4),
            "projected_stockout_days": round(stockout_days, 2) if stockout_days is not None else None,
            "movement_count": len(movements),
            "explanation": explanation,
            "limitations": limitations,
        }

    def forecast(self, db: Session, inventory_id: int, horizon_days: int) -> InventoryForecastResponse:
        record = db.get(Inventory, inventory_id)
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventory record not found")
        return InventoryForecastResponse(**self._calculate(db, record, horizon_days))

    def recommendations(self, db: Session, horizon_days: int) -> List[InventoryRecommendationResponse]:
        records = db.query(Inventory).order_by(Inventory.id.asc()).all()
        recommendations = []
        for record in records:
            values = self._calculate(db, record, horizon_days)
            reorder_quantity = max(0, record.reorder_level - record.quantity)
            if values["data_sufficiency"] == "sufficient":
                reorder_quantity = max(
                    reorder_quantity,
                    ceil(record.reorder_level + values["average_daily_demand"] * horizon_days - record.quantity),
                )
            values["recommendation_status"] = "REORDER" if values["reorder_recommended"] else "MONITOR"
            values["recommended_reorder_quantity"] = reorder_quantity
            recommendations.append(InventoryRecommendationResponse(**values))
        return recommendations


inventory_forecast_service = InventoryForecastService()
