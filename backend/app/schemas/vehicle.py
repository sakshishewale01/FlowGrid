"""
Vehicle Schemas
===============
Pydantic schemas for fleet vehicle registration, updates, and serialized responses.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class VehicleBase(BaseModel):
    """
    Shared attributes for fleet vehicles.
    """
    registration_number: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="License plate or unique fleet registration identifier",
        examples=["FL-TX-8821"],
    )
    vehicle_type: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Classification of the transport unit (e.g. Semi-Trailer, Box Truck, Van)",
        examples=["Semi-Trailer"],
    )
    capacity: Decimal = Field(
        ...,
        gt=0,
        decimal_places=2,
        max_digits=10,
        description="Maximum carrying capacity in kilograms (must be greater than 0)",
        examples=[18000.00],
    )
    status: str = Field(
        default="AVAILABLE",
        min_length=2,
        max_length=20,
        description="Current fleet operational status (e.g. AVAILABLE, IN_USE, MAINTENANCE, DECOMMISSIONED)",
        examples=["AVAILABLE"],
    )


class VehicleCreate(VehicleBase):
    """
    Payload for registering a new fleet vehicle (POST /api/v1/vehicles).
    Accessible to ADMIN and MANAGER roles.
    """
    pass


class VehicleUpdate(BaseModel):
    """
    Payload for updating an existing vehicle (PUT/PATCH /api/v1/vehicles/{id}).
    All fields are optional.
    """
    registration_number: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=50,
        description="Updated registration identifier",
    )
    vehicle_type: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=50,
        description="Updated vehicle type",
    )
    capacity: Optional[Decimal] = Field(
        default=None,
        gt=0,
        decimal_places=2,
        max_digits=10,
        description="Updated carrying capacity (must be greater than 0)",
    )
    status: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=20,
        description="Updated vehicle operational status",
    )


class VehicleResponse(VehicleBase):
    """
    Response schema returning complete fleet vehicle details.
    """
    id: int = Field(..., description="Unique primary key of the vehicle record")
    created_at: datetime = Field(..., description="Timestamp when record was created")
    updated_at: datetime = Field(..., description="Timestamp when record was last updated")

    model_config = ConfigDict(from_attributes=True)
