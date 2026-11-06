"""Schemas for vehicle maintenance scheduling and history."""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


VALID_MAINTENANCE_STATUSES = {"SCHEDULED", "IN_PROGRESS", "COMPLETED", "CANCELLED"}


class VehicleMaintenanceCreate(BaseModel):
    service_type: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=2000)
    scheduled_date: date
    status: str = Field(default="SCHEDULED")

    @field_validator("service_type")
    @classmethod
    def validate_service_type(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Service type cannot be empty")
        return value

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        value = value.strip().upper()
        if value not in VALID_MAINTENANCE_STATUSES:
            raise ValueError("Invalid maintenance status")
        return value


class VehicleMaintenanceUpdate(BaseModel):
    service_type: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=2000)
    scheduled_date: Optional[date] = None
    completed_at: Optional[datetime] = None
    status: Optional[str] = None

    @field_validator("service_type")
    @classmethod
    def validate_service_type(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not value.strip():
            raise ValueError("Service type cannot be empty")
        return value.strip() if value is not None else value

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: Optional[str]) -> Optional[str]:
        if value is not None:
            value = value.strip().upper()
            if value not in VALID_MAINTENANCE_STATUSES:
                raise ValueError("Invalid maintenance status")
        return value


class VehicleMaintenanceResponse(BaseModel):
    id: int
    vehicle_id: int
    service_type: str
    description: Optional[str]
    scheduled_date: date
    completed_at: Optional[datetime]
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
