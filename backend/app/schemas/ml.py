"""
FlowGrid AI - Machine Learning Prediction Schemas
=================================================
Pydantic models defining input validation and structured prediction responses
for the shipment delay classification service.
"""

from datetime import date
from typing import Dict, Any, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


class DelayPredictionRequest(BaseModel):
    """
    Input payload for the delay prediction service.
    Accepts validated shipment features supported by the trained model pipeline.
    Does not allow silent defaulting of required logistics context.
    """
    warehouse: str = Field(
        ...,
        min_length=1,
        description="Origin warehouse facility name (e.g., 'East Depot - Kolkata')",
        examples=["East Depot - Kolkata"],
    )
    destination: str = Field(
        ...,
        min_length=1,
        description="Destination logistics hub or depot (e.g., 'Jaipur Commerce Center')",
        examples=["Jaipur Commerce Center"],
    )
    transport_mode: str = Field(
        ...,
        min_length=1,
        description="Vehicle classification (e.g., 'Mini Truck (Tata Ace class)')",
        examples=["Mini Truck (Tata Ace class)"],
    )
    distance_km: float = Field(
        ...,
        gt=0.0,
        description="Corridor transit distance in kilometers (must be > 0)",
        examples=[1765.1],
    )
    supplier: str = Field(
        ...,
        min_length=1,
        description="Carrier or supplier partner name (e.g., 'Orion Freight Co.')",
        examples=["Orion Freight Co."],
    )
    driver: str = Field(
        ...,
        min_length=1,
        description="Assigned driver alias or identifier (e.g., 'A. Kumar')",
        examples=["A. Kumar"],
    )
    dispatch_date: Optional[date] = Field(
        default=None,
        description="Calendar dispatch date (YYYY-MM-DD). If omitted, both month and day_of_week must be explicitly supplied.",
        examples=["2026-10-15"],
    )
    month: Optional[int] = Field(
        default=None,
        ge=1,
        le=12,
        description="Calendar month (1-12). Required if dispatch_date is omitted.",
        examples=[10],
    )
    day_of_week: Optional[int] = Field(
        default=None,
        ge=0,
        le=6,
        description="Day of week (0=Monday, 6=Sunday). Required if dispatch_date is omitted.",
        examples=[3],
    )

    @model_validator(mode="after")
    def validate_temporal_features(self) -> "DelayPredictionRequest":
        """
        Ensures temporal features are strictly grounded: either through a valid dispatch_date
        or explicit month and day_of_week inputs. No silent invention of calendar data.
        """
        if self.dispatch_date is not None:
            self.month = self.dispatch_date.month
            self.day_of_week = self.dispatch_date.weekday()
        elif self.month is None or self.day_of_week is None:
            raise ValueError(
                "Incomplete temporal features: must provide either 'dispatch_date' or both ('month', 'day_of_week'). "
                "FlowGrid AI does not silently invent missing calendar features."
            )
        return self

    def to_feature_dict(self) -> Dict[str, Any]:
        """
        Transforms validated schema into the exact dictionary required by the model vectorizer.
        """
        is_weekend = 1.0 if self.day_of_week is not None and self.day_of_week >= 5 else 0.0
        return {
            "warehouse": self.warehouse.strip(),
            "destination": self.destination.strip(),
            "transport_mode": self.transport_mode.strip(),
            "supplier": self.supplier.strip(),
            "driver": self.driver.strip(),
            "distance_km": float(self.distance_km),
            "month": float(self.month),
            "day_of_week": float(self.day_of_week),
            "is_weekend": is_weekend,
        }

    model_config = ConfigDict(from_attributes=True)


class DelayPredictionResponse(BaseModel):
    """
    Response schema returning binary delay prediction, risk probability score,
    qualitative tier, and explicit prototype governance disclosure.
    """
    is_delayed: bool = Field(
        ...,
        description="Binary prediction: True if predicted to experience transit delay, False otherwise",
    )
    delay_probability: float = Field(
        ...,
        description="Model confidence score / probability of delay (0.0 to 1.0)",
    )
    risk_level: str = Field(
        ...,
        description="Qualitative delay risk band: LOW (< 0.25), MEDIUM (0.25 - 0.50), HIGH (> 0.50)",
    )
    model_version: str = Field(
        ...,
        description="Deployed model artifact identifier and architecture",
    )
    explanation: str = Field(
        ...,
        description="Technical transparency notice regarding synthetic benchmark training",
    )
    features_used: Dict[str, Any] = Field(
        ...,
        description="Dictionary of features processed by the model pipeline",
    )

    model_config = ConfigDict(from_attributes=True)
