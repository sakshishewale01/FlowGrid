"""Transparent inventory forecast and movement schemas."""

from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class InventoryForecastResponse(BaseModel):
    inventory_id: int
    product_id: int
    warehouse_id: int
    horizon_days: int
    forecast_quantity: float
    current_quantity: int
    reorder_level: int
    reorder_recommended: bool
    data_sufficiency: str
    average_daily_demand: float
    projected_stockout_days: float | None
    movement_count: int
    explanation: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)


class InventoryRecommendationResponse(InventoryForecastResponse):
    recommendation_status: str
    recommended_reorder_quantity: int


class InventoryMovementResponse(BaseModel):
    id: int
    inventory_id: int
    quantity_delta: int
    quantity_before: int
    quantity_after: int
    reason: str
    note: str | None
    created_by_user_id: int | None
    created_at: datetime
