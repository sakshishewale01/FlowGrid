"""Transparent inventory forecast prototype schemas."""

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
    explanation: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
