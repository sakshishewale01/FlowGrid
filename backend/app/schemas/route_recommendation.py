"""Schemas for explainable, database-grounded route recommendations."""

from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, model_validator


class RouteRecommendationRequest(BaseModel):
    origin: Optional[str] = Field(default=None, min_length=1, max_length=255)
    destination: Optional[str] = Field(default=None, min_length=1, max_length=255)
    shipment_id: Optional[int] = Field(default=None, gt=0)
    shipment_weight_kg: Optional[Decimal] = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    vehicle_id: Optional[int] = Field(default=None, gt=0)
    limit: int = Field(default=5, ge=1, le=20)

    @model_validator(mode="after")
    def require_corridor_or_shipment(self):
        if self.shipment_id is None and (not self.origin or not self.destination):
            raise ValueError("Provide origin and destination, or a shipment_id")
        return self


class RouteRecommendation(BaseModel):
    route_id: int
    route_name: str
    origin: str
    destination: str
    estimated_distance: Optional[Decimal]
    estimated_duration: Optional[Decimal]
    score: float
    explanation: List[str]
    vehicle_id: Optional[int] = None
    vehicle_capacity_kg: Optional[Decimal] = None
    shipment_id: Optional[int] = None
    capacity_feasible: bool = True
    constraints: List[str] = Field(default_factory=list)
    estimated_only: bool = True


class RouteRecommendationResponse(BaseModel):
    recommendations: List[RouteRecommendation]
    methodology: str
    limitations: List[str]


class RouteRecommendationApproval(BaseModel):
    shipment_id: int = Field(..., gt=0)
    vehicle_id: Optional[int] = Field(default=None, gt=0)


class RouteRecommendationApprovalResponse(BaseModel):
    route_id: int
    shipment_id: int
    vehicle_id: Optional[int]
    message: str
