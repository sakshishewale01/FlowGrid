"""Inventory forecast prototype grounded in currently available inventory data."""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.inventory import Inventory
from app.schemas.inventory_forecast import InventoryForecastResponse


class InventoryForecastService:
    def forecast(self, db: Session, inventory_id: int, horizon_days: int) -> InventoryForecastResponse:
        record = db.get(Inventory, inventory_id)
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventory record not found")
        forecast_quantity = float(record.reorder_level)
        return InventoryForecastResponse(
            inventory_id=record.id,
            product_id=record.product_id,
            warehouse_id=record.warehouse_id,
            horizon_days=horizon_days,
            forecast_quantity=forecast_quantity,
            current_quantity=record.quantity,
            reorder_level=record.reorder_level,
            reorder_recommended=record.quantity <= record.reorder_level,
            data_sufficiency="insufficient",
            explanation=[
                "Historical demand observations are not stored in the current inventory schema.",
                "The prototype uses the configured reorder level as a transparent planning baseline.",
            ],
            limitations=[
                "This is not a demand forecast and must not be interpreted as production forecasting accuracy.",
                "Add validated historical demand data before using statistical or machine-learning forecasting.",
            ],
        )


inventory_forecast_service = InventoryForecastService()
