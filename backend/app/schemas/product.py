"""
Product Schemas
===============
Pydantic models for product catalog creation, updates, and serialized responses.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ProductBase(BaseModel):
    """
    Shared attributes for product models.
    """
    name: str = Field(
        ...,
        min_length=2,
        max_length=150,
        description="Official name of the product item",
        examples=["Heavy Duty Hydraulic Pallet Jack"],
    )
    sku: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Unique Stock Keeping Unit (SKU) identifier",
        examples=["PLT-JK-2000"],
    )
    description: Optional[str] = Field(
        default=None,
        description="Optional detailed product specification or description",
        examples=["Hydraulic manual pallet jack with 2000kg load capacity."],
    )
    unit_price: Decimal = Field(
        ...,
        ge=0,
        decimal_places=2,
        max_digits=10,
        description="Unit price (must be greater than or equal to 0.00)",
        examples=[349.99],
    )
    is_active: bool = Field(
        default=True,
        description="Operational catalog active status",
    )


class ProductCreate(ProductBase):
    """
    Payload for creating a new product (POST /api/v1/products).
    Accessible to ADMIN and MANAGER roles.
    """
    pass


class ProductUpdate(BaseModel):
    """
    Payload for updating an existing product (PUT/PATCH /api/v1/products/{id}).
    All fields are optional; only provided fields are updated.
    """
    name: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=150,
        description="Updated name of the product item",
    )
    sku: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=50,
        description="Updated Stock Keeping Unit (SKU)",
    )
    description: Optional[str] = Field(
        default=None,
        description="Updated description or specifications",
    )
    unit_price: Optional[Decimal] = Field(
        default=None,
        ge=0,
        decimal_places=2,
        max_digits=10,
        description="Updated unit price (>= 0.00)",
    )
    is_active: Optional[bool] = Field(
        default=None,
        description="Updated active status",
    )


class ProductResponse(ProductBase):
    """
    Response schema returning complete product catalog details.
    """
    id: int = Field(..., description="Unique primary key of the product")
    created_at: datetime = Field(..., description="Timestamp when record was created")
    updated_at: datetime = Field(..., description="Timestamp when record was last updated")

    model_config = ConfigDict(from_attributes=True)
