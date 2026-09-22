"""
Driver Schemas
==============
Pydantic schemas for driver profiles, creation, updates, and serialized responses.
"""

from datetime import datetime
from typing import Optional, Set
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.models.user import UserRole


VALID_DRIVER_STATUSES: Set[str] = {
    "AVAILABLE",
    "ON_DUTY",
    "IN_TRANSIT",
    "OFF_DUTY",
    "SUSPENDED",
}


class UserDriverSummary(BaseModel):
    """
    Compact user summary nested inside driver response.
    """
    id: int
    name: str
    email: str
    role: UserRole
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class DriverBase(BaseModel):
    """
    Shared attributes for driver profile models.
    """
    user_id: int = Field(
        ...,
        gt=0,
        description="ID of the user account linked to this driver profile",
        examples=[3],
    )
    license_number: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Commercial or standard driver's license number",
        examples=["DL-948201-TX"],
    )
    phone_number: str = Field(
        ...,
        min_length=7,
        max_length=25,
        description="Contact phone number for mobile dispatch",
        examples=["+1-555-234-5678"],
    )
    availability_status: str = Field(
        default="AVAILABLE",
        min_length=2,
        max_length=20,
        description="Current operational status (e.g. AVAILABLE, ON_DUTY, IN_TRANSIT, OFF_DUTY, SUSPENDED)",
        examples=["AVAILABLE"],
    )

    @field_validator("license_number", "phone_number", mode="before")
    @classmethod
    def sanitize_strings(cls, v: str) -> str:
        if isinstance(v, str):
            cleaned = v.strip()
            if not cleaned:
                raise ValueError("Value cannot be blank or whitespace-only")
            return cleaned
        return v

    @field_validator("availability_status", mode="before")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if isinstance(v, str):
            cleaned = v.strip().upper()
            if cleaned not in VALID_DRIVER_STATUSES:
                raise ValueError(
                    f"Invalid driver availability status '{v}'. Allowed statuses: {sorted(list(VALID_DRIVER_STATUSES))}"
                )
            return cleaned
        return v


class DriverCreate(DriverBase):
    """
    Payload for creating a driver profile (POST /api/v1/drivers).
    Accessible to ADMIN and MANAGER roles.
    """
    pass


class DriverUpdate(BaseModel):
    """
    Payload for updating an existing driver profile (PUT/PATCH /api/v1/drivers/{id}).
    All fields are optional.
    """
    license_number: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=50,
        description="Updated driver license number",
    )
    phone_number: Optional[str] = Field(
        default=None,
        min_length=7,
        max_length=25,
        description="Updated contact phone number",
    )
    availability_status: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=20,
        description="Updated availability status",
    )

    @field_validator("license_number", "phone_number", mode="before")
    @classmethod
    def sanitize_strings(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and isinstance(v, str):
            cleaned = v.strip()
            if not cleaned:
                raise ValueError("Value cannot be blank or whitespace-only")
            return cleaned
        return v

    @field_validator("availability_status", mode="before")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and isinstance(v, str):
            cleaned = v.strip().upper()
            if cleaned not in VALID_DRIVER_STATUSES:
                raise ValueError(
                    f"Invalid driver availability status '{v}'. Allowed statuses: {sorted(list(VALID_DRIVER_STATUSES))}"
                )
            return cleaned
        return v


class DriverResponse(BaseModel):
    """
    Response schema returning complete driver profile details.
    """
    id: int = Field(..., description="Unique primary key of the driver record")
    user_id: int = Field(..., description="Linked user ID")
    license_number: str = Field(..., description="Driver license number")
    phone_number: str = Field(..., description="Driver phone number")
    availability_status: str = Field(..., description="Operational availability status")
    created_at: datetime = Field(..., description="Timestamp when record was created")
    updated_at: datetime = Field(..., description="Timestamp when record was last updated")
    user: Optional[UserDriverSummary] = Field(default=None, description="Linked user account details")

    model_config = ConfigDict(from_attributes=True)
