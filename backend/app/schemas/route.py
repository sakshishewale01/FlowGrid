"""
Route Schemas
=============
Pydantic schemas for route creation, updates, serialized responses,
and shipment assignment payloads.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.route import RouteStatus
from app.schemas.shipment import ShipmentResponse


class RouteBase(BaseModel):
    """
    Shared attributes for transit corridors and logistics routes.
    """
    name: str = Field(
        ...,
        min_length=1,
        max_length=150,
        description="Descriptive route or corridor name",
        examples=["I-80 Midwest Freight Corridor"],
    )
    origin: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Origin hub, warehouse facility, or starting city",
        examples=["Chicago, IL"],
    )
    destination: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Destination terminal, facility, or ending city",
        examples=["Newark, NJ"],
    )
    estimated_distance: Optional[Decimal] = Field(
        default=None,
        ge=0,
        decimal_places=2,
        max_digits=10,
        description="Estimated route distance (e.g., kilometers or miles)",
        examples=[1280.50],
    )
    estimated_duration: Optional[Decimal] = Field(
        default=None,
        ge=0,
        decimal_places=2,
        max_digits=10,
        description="Estimated transit duration (e.g., hours)",
        examples=[18.50],
    )
    status: RouteStatus = Field(
        default=RouteStatus.ACTIVE,
        description="Current operational status of the route",
        examples=[RouteStatus.ACTIVE],
    )


class RouteCreate(RouteBase):
    """
    Payload for creating a new route. Validates non-empty strings and non-negative metrics.
    """
    @field_validator("name", "origin", "destination")
    @classmethod
    def validate_non_empty_strings(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Field cannot be empty or solely whitespace")
        return stripped

    @field_validator("estimated_distance", "estimated_duration")
    @classmethod
    def validate_non_negative_metrics(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None and v < 0:
            raise ValueError("Estimated metric must be greater than or equal to 0")
        return v


class RouteUpdate(BaseModel):
    """
    Payload for updating an existing route (PUT / PATCH).
    """
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=150,
        description="Updated route name",
    )
    origin: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Updated origin location",
    )
    destination: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Updated destination location",
    )
    estimated_distance: Optional[Decimal] = Field(
        default=None,
        ge=0,
        decimal_places=2,
        max_digits=10,
        description="Updated estimated route distance",
    )
    estimated_duration: Optional[Decimal] = Field(
        default=None,
        ge=0,
        decimal_places=2,
        max_digits=10,
        description="Updated estimated transit duration",
    )
    status: Optional[RouteStatus] = Field(
        default=None,
        description="Updated operational status",
    )
    is_active: Optional[bool] = Field(
        default=None,
        description="Active/inactive status flag",
    )

    @field_validator("name", "origin", "destination")
    @classmethod
    def validate_non_empty_strings(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            stripped = v.strip()
            if not stripped:
                raise ValueError("Field cannot be empty or solely whitespace")
            return stripped
        return v

    @field_validator("estimated_distance", "estimated_duration")
    @classmethod
    def validate_non_negative_metrics(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None and v < 0:
            raise ValueError("Estimated metric must be greater than or equal to 0")
        return v


class RouteResponse(RouteBase):
    """
    Response schema returning complete route details.
    """
    id: int = Field(..., description="Unique primary key of the route")
    is_active: bool = Field(..., description="Active operational record flag")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last modification timestamp")
    shipments_count: Optional[int] = Field(
        default=None,
        description="Number of active shipments assigned to this route",
    )

    model_config = ConfigDict(from_attributes=True)


class RouteDetailResponse(RouteResponse):
    """
    Detailed response schema including assigned shipments.
    """
    shipments: List[ShipmentResponse] = Field(
        default_factory=list,
        description="List of shipments currently allocated to this route",
    )


class RouteShipmentAssign(BaseModel):
    """
    Payload for allocating one or more shipments to a route.
    Supports both batch assignment via `shipment_ids` or single assignment via `shipment_id`.
    """
    shipment_ids: Optional[List[int]] = Field(
        default=None,
        description="List of shipment IDs to assign to the route",
        examples=[[1, 2, 3]],
    )
    shipment_id: Optional[int] = Field(
        default=None,
        gt=0,
        description="Single shipment ID to assign to the route",
        examples=[1],
    )

    @model_validator(mode="after")
    def validate_and_normalize_ids(self) -> "RouteShipmentAssign":
        ids: List[int] = []
        if self.shipment_ids is not None:
            ids.extend(self.shipment_ids)
        if self.shipment_id is not None:
            ids.append(self.shipment_id)
        if not ids:
            raise ValueError("At least one shipment ID must be provided via 'shipment_ids' or 'shipment_id'")
        return self

    def get_ids(self) -> List[int]:
        ids: List[int] = []
        if self.shipment_ids is not None:
            ids.extend(self.shipment_ids)
        if self.shipment_id is not None and self.shipment_id not in ids:
            ids.append(self.shipment_id)
        return ids
