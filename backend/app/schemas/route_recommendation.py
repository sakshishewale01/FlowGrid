"""Schemas for explainable, database-grounded route recommendations."""

from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


class RouteRecommendationRequest(BaseModel):
    origin: str = Field(..., min_length=1, max_length=255)
    destination: str = Field(..., min_length=1, max_length=255)
    shipment_weight_kg: Optional[Decimal] = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    vehicle_id: Optional[int] = Field(default=None, gt=0)
    limit: int = Field(default=5, ge=1, le=20)


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
    estimated_only: bool = True


class RouteRecommendationResponse(BaseModel):
    recommendations: List[RouteRecommendation]
    methodology: str
    limitations: List[str]
