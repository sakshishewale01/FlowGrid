"""
Warehouse Schemas
=================
Pydantic models for warehouse creation, modification, and response serialization.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class WarehouseBase(BaseModel):
    """
    Shared attributes for warehouse models.
    """
    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Official name or identifier of the warehouse facility",
        examples=["Chicago Central Hub"],
    )
    location: str = Field(
        ...,
        min_length=2,
        max_length=150,
        description="Geographic region or metropolitan area",
        examples=["Chicago, IL"],
    )
    address: str = Field(
        ...,
        min_length=3,
        max_length=255,
        description="Street address of the facility",
        examples=["1200 Logistics Blvd, Dock 4, Chicago, IL 60601"],
    )
    capacity: int = Field(
        ...,
        gt=0,
        le=50000000,
        description="Total storage capacity in square feet or pallet units (must be > 0 and <= 50,000,000)",
        examples=[50000],
    )
    is_active: bool = Field(
        default=True,
        description="Operational status of the warehouse facility",
    )

    @field_validator("name", "location", "address", mode="before")
    @classmethod
    def sanitize_strings(cls, v: str) -> str:
        if isinstance(v, str):
            cleaned = v.strip()
            if not cleaned:
                raise ValueError("Value cannot be blank or whitespace-only")
            return cleaned
        return v


class WarehouseCreate(WarehouseBase):
    """
    Payload for creating a new warehouse (POST /api/v1/warehouses).
    Requires Admin or Manager role.
    """
    pass


class WarehouseUpdate(BaseModel):
    """
    Payload for updating an existing warehouse (PUT/PATCH /api/v1/warehouses/{id}).
    All fields are optional; only provided fields are updated.
    """
    name: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100,
        description="Updated name of the facility",
    )
    location: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=150,
        description="Updated geographic region",
    )
    address: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=255,
        description="Updated street address",
    )
    capacity: Optional[int] = Field(
        default=None,
        gt=0,
        le=50000000,
        description="Updated storage capacity (must be > 0 and <= 50,000,000)",
    )
    is_active: Optional[bool] = Field(
        default=None,
        description="Updated operational status",
    )

    @field_validator("name", "location", "address", mode="before")
    @classmethod
    def sanitize_strings(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and isinstance(v, str):
            cleaned = v.strip()
            if not cleaned:
                raise ValueError("Value cannot be blank or whitespace-only")
            return cleaned
        return v


class WarehouseResponse(WarehouseBase):
    """
    Response schema returning complete warehouse details.
    """
    id: int = Field(..., description="Unique primary key of the warehouse")
    created_at: datetime = Field(..., description="Timestamp when record was created")
    updated_at: datetime = Field(..., description="Timestamp when record was last updated")

    model_config = ConfigDict(from_attributes=True)
