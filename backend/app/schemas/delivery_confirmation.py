"""
Proof of Delivery Schemas
=========================
Validated request and response models for delivery confirmations.
"""

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DeliveryConfirmationCreate(BaseModel):
    """Payload submitted by an assigned driver or authorized operator."""

    recipient_name: str = Field(..., min_length=2, max_length=150)
    delivered_at: datetime
    delivery_notes: Optional[str] = Field(default=None, max_length=2000)
    evidence_metadata: Optional[dict[str, str]] = Field(
        default=None,
        description=(
            "Optional descriptive evidence metadata only. File uploads, photos, "
            "signatures, and private evidence storage are not supported."
        ),
    )

    @field_validator("recipient_name", mode="before")
    @classmethod
    def validate_recipient_name(cls, value: str) -> str:
        if not isinstance(value, str):
            return value
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Recipient name cannot be blank")
        return cleaned

    @field_validator("delivery_notes", mode="before")
    @classmethod
    def normalize_delivery_notes(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("delivered_at")
    @classmethod
    def validate_delivered_at(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Delivery timestamp must be timezone-aware")
        if value > datetime.now(timezone.utc):
            raise ValueError("Delivery timestamp cannot be in the future")
        return value

    @field_validator("evidence_metadata")
    @classmethod
    def validate_evidence_metadata(
        cls,
        value: Optional[dict[str, str]],
    ) -> Optional[dict[str, str]]:
        if value is None:
            return None
        if len(value) > 10:
            raise ValueError("Evidence metadata cannot contain more than 10 entries")
        normalized: dict[str, str] = {}
        for key, item in value.items():
            clean_key = key.strip()
            clean_item = item.strip()
            if not clean_key or not clean_item:
                raise ValueError("Evidence metadata keys and values cannot be blank")
            normalized[clean_key] = clean_item
        return normalized


class DeliveryConfirmationResponse(BaseModel):
    """Serialized delivery confirmation details."""

    id: int
    shipment_id: int
    submitted_by_user_id: int
    recipient_name: str
    delivered_at: datetime
    delivery_notes: Optional[str] = None
    evidence_metadata: Optional[dict[str, str]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
