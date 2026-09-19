"""
Inventory Schemas
=================
Pydantic schemas for inventory creation, updates, and serialized responses.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class InventoryBase(BaseModel):
    """
    Shared attributes for inventory items.
    """
    warehouse_id: int = Field(
        ...,
        gt=0,
        description="Primary key ID of the associated warehouse facility",
        examples=[1],
    )
    product_id: int = Field(
        ...,
        gt=0,
        description="Primary key ID of the commercial product item",
        examples=[1],
    )
    quantity: int = Field(
        default=0,
        ge=0,
        description="On-hand stock balance (must be greater than or equal to 0)",
        examples=[100],
    )
    reorder_level: int = Field(
        default=10,
        ge=0,
        description="Threshold below which reordering is triggered (must be greater than or equal to 0)",
        examples=[15],
    )


class InventoryCreate(InventoryBase):
    """
    Payload for creating an inventory stock record (POST /api/v1/inventory).
    Accessible to ADMIN and MANAGER roles.
    """
    pass


class InventoryUpdate(BaseModel):
    """
    Payload for updating inventory stock and threshold levels (PUT/PATCH /api/v1/inventory/{id}).
    All fields are optional; only provided values are updated.
    """
    quantity: Optional[int] = Field(
        default=None,
        ge=0,
        description="Updated on-hand stock quantity (>= 0)",
        examples=[120],
    )
    reorder_level: Optional[int] = Field(
        default=None,
        ge=0,
        description="Updated replenishment threshold (>= 0)",
        examples=[20],
    )


class WarehouseSummary(BaseModel):
    """
    Compact warehouse summary nested in inventory response.
    """
    id: int
    name: str
    location: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class ProductSummary(BaseModel):
    """
    Compact product summary nested in inventory response.
    """
    id: int
    name: str
    sku: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class InventoryResponse(BaseModel):
    """
    Response schema returning complete inventory record with optional relationship details.
    """
    id: int = Field(..., description="Unique primary key of the inventory record")
    warehouse_id: int = Field(..., description="Associated warehouse facility ID")
    product_id: int = Field(..., description="Associated product item ID")
    quantity: int = Field(..., description="Current on-hand stock balance")
    reorder_level: int = Field(..., description="Stock replenishment threshold")
    updated_at: datetime = Field(..., description="Timestamp when record was last updated")
    warehouse: Optional[WarehouseSummary] = Field(default=None, description="Summary of warehouse facility")
    product: Optional[ProductSummary] = Field(default=None, description="Summary of product item")

    model_config = ConfigDict(from_attributes=True)
