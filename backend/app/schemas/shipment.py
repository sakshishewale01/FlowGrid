"""
Shipment Schemas
================
Pydantic schemas for shipment creation, updates, status transitions, and serialized responses.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.shipment import ShipmentStatus


class WarehouseShipmentSummary(BaseModel):
    id: int
    name: str
    location: str
    is_active: bool
    model_config = ConfigDict(from_attributes=True)


class DriverShipmentSummary(BaseModel):
    id: int
    license_number: str
    phone_number: str
    availability_status: str
    model_config = ConfigDict(from_attributes=True)


class VehicleShipmentSummary(BaseModel):
    id: int
    registration_number: str
    vehicle_type: str
    capacity: Decimal
    status: str
    model_config = ConfigDict(from_attributes=True)


class ShipmentBase(BaseModel):
    """
    Shared attributes for shipment records.
    """
    origin_warehouse_id: Optional[int] = Field(
        default=None,
        gt=0,
        description="ID of the departure/dispatch warehouse facility",
        examples=[1],
    )
    destination_address: str = Field(
        ...,
        min_length=3,
        max_length=255,
        description="Delivery street address",
        examples=["742 Evergreen Terrace"],
    )
    destination_city: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Consignee destination city",
        examples=["Springfield"],
    )
    destination_state: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Consignee state or province",
        examples=["IL"],
    )
    destination_postal_code: str = Field(
        ...,
        min_length=2,
        max_length=20,
        description="Consignee ZIP or postal code",
        examples=["62704"],
    )
    assigned_driver_id: Optional[int] = Field(
        default=None,
        gt=0,
        description="Allocated driver ID",
        examples=[1],
    )
    assigned_vehicle_id: Optional[int] = Field(
        default=None,
        gt=0,
        description="Allocated vehicle ID",
        examples=[1],
    )
    total_weight_kg: Optional[Decimal] = Field(
        default=None,
        gt=0,
        le=100000,
        decimal_places=2,
        max_digits=10,
        description="Total cargo weight in kilograms (must be positive, <= 100,000 kg)",
        examples=[450.00],
    )
    total_volume_cbm: Optional[Decimal] = Field(
        default=None,
        gt=0,
        le=1000,
        decimal_places=2,
        max_digits=10,
        description="Total cargo volume in cubic meters (must be positive, <= 1,000 cbm)",
        examples=[3.20],
    )
    scheduled_pickup_at: Optional[datetime] = Field(
        default=None,
        description="Scheduled pickup window timestamp",
    )

    @field_validator(
        "destination_address",
        "destination_city",
        "destination_state",
        "destination_postal_code",
        mode="before",
    )
    @classmethod
    def sanitize_strings(cls, v: str) -> str:
        if isinstance(v, str):
            cleaned = v.strip()
            if not cleaned:
                raise ValueError("Value cannot be blank or whitespace-only")
            return cleaned
        return v

    @field_validator("scheduled_pickup_at", mode="before")
    @classmethod
    def validate_scheduled_date(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v is None:
            return None
        if isinstance(v, str):
            v = datetime.fromisoformat(v)
        if isinstance(v, datetime) and v.year < 2020:
            raise ValueError("Scheduled pickup timestamp cannot be earlier than year 2020")
        return v


class ShipmentCreate(ShipmentBase):
    """
    Payload for creating a new shipment.
    Tracking number is automatically generated if omitted.
    """
    tracking_number: Optional[str] = Field(
        default=None,
        min_length=6,
        max_length=60,
        description="Optional pre-assigned tracking number; generated if omitted",
        examples=["FG-20260919-AB12CD34"],
    )

    @field_validator("tracking_number", mode="before")
    @classmethod
    def sanitize_tracking(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and isinstance(v, str):
            cleaned = v.strip()
            if not cleaned:
                return None
            return cleaned.upper()
        return v


class ShipmentUpdate(BaseModel):
    """
    Payload for updating shipment details (PUT/PATCH /api/v1/shipments/{id}).
    Allowed only before delivery.
    """
    origin_warehouse_id: Optional[int] = Field(default=None, gt=0)
    destination_address: Optional[str] = Field(default=None, min_length=3, max_length=255)
    destination_city: Optional[str] = Field(default=None, min_length=2, max_length=100)
    destination_state: Optional[str] = Field(default=None, min_length=2, max_length=100)
    destination_postal_code: Optional[str] = Field(default=None, min_length=2, max_length=20)
    assigned_driver_id: Optional[int] = Field(default=None, gt=0)
    assigned_vehicle_id: Optional[int] = Field(default=None, gt=0)
    total_weight_kg: Optional[Decimal] = Field(default=None, gt=0, le=100000)
    total_volume_cbm: Optional[Decimal] = Field(default=None, gt=0, le=1000)
    scheduled_pickup_at: Optional[datetime] = None

    @field_validator(
        "destination_address",
        "destination_city",
        "destination_state",
        "destination_postal_code",
        mode="before",
    )
    @classmethod
    def sanitize_strings(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and isinstance(v, str):
            cleaned = v.strip()
            if not cleaned:
                raise ValueError("Value cannot be blank or whitespace-only")
            return cleaned
        return v

    @field_validator("scheduled_pickup_at", mode="before")
    @classmethod
    def validate_scheduled_date(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v is None:
            return None
        if isinstance(v, str):
            v = datetime.fromisoformat(v)
        if isinstance(v, datetime) and v.year < 2020:
            raise ValueError("Scheduled pickup timestamp cannot be earlier than year 2020")
        return v



class ShipmentStatusUpdate(BaseModel):
    """
    Payload for advancing shipment lifecycle state.
    Must follow strict state machine rules.
    """
    status: ShipmentStatus = Field(
        ...,
        description="Target lifecycle state",
        examples=[ShipmentStatus.CONFIRMED],
    )
    remarks: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Optional status change audit notes or remarks",
        examples=["Driver picked up cargo at Chicago terminal"],
    )



class ShipmentResponse(ShipmentBase):
    """
    Response schema returning complete shipment details.
    """
    id: int = Field(..., description="Unique primary key of the shipment")
    tracking_number: str = Field(..., description="Unique human-readable tracking number")
    status: ShipmentStatus = Field(..., description="Current lifecycle state")
    delivered_at: Optional[datetime] = Field(default=None, description="Delivery completion timestamp")
    is_active: bool = Field(..., description="Active operational record status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last modification timestamp")
    origin_warehouse: Optional[WarehouseShipmentSummary] = Field(default=None, description="Origin warehouse details")
    assigned_driver: Optional[DriverShipmentSummary] = Field(default=None, description="Assigned driver details")
    assigned_vehicle: Optional[VehicleShipmentSummary] = Field(default=None, description="Assigned vehicle details")

    model_config = ConfigDict(from_attributes=True)
