"""
Tracking and Status History Schemas
===================================
Pydantic validation schemas for status audit trails and physical tracking events.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.shipment import ShipmentStatus


class UserSummary(BaseModel):
    """
    Lightweight user profile for audit references.
    """
    id: int = Field(..., description="User ID")
    name: str = Field(..., description="Full name of user")
    email: str = Field(..., description="User email address")
    role: str = Field(..., description="Role of the user at the time of change")

    model_config = ConfigDict(from_attributes=True)


class ShipmentStatusHistoryResponse(BaseModel):
    """
    Audit record representing a single lifecycle state transition.
    """
    id: int = Field(..., description="Status history record ID")
    shipment_id: int = Field(..., description="Associated shipment ID")
    previous_status: Optional[ShipmentStatus] = Field(
        default=None,
        description="Previous lifecycle state (null if initial registration)",
    )
    new_status: ShipmentStatus = Field(
        ...,
        description="Target lifecycle state transitioned to",
    )
    changed_by_user_id: Optional[int] = Field(
        default=None,
        description="ID of the user who initiated the status change",
    )
    changed_by: Optional[UserSummary] = Field(
        default=None,
        description="Profile details of the user who made the change",
    )
    remarks: Optional[str] = Field(
        default=None,
        description="Operational remarks, notes, or cancellation reason",
    )
    created_at: datetime = Field(..., description="Timestamp when the transition occurred")

    model_config = ConfigDict(from_attributes=True)


class ShipmentTrackingEventCreate(BaseModel):
    """
    Payload for recording a physical or milestone tracking event.
    """
    event_type: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Category of tracking event (e.g., CHECKPOINT, SCAN, DEPARTED, ARRIVED, DELAY, EXCEPTION)",
        examples=["CHECKPOINT"],
    )
    location: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="Location, hub, transit facility, or city",
        examples=["Distribution Center, Chicago, IL"],
    )
    description: str = Field(
        ...,
        min_length=2,
        max_length=500,
        description="Detailed description of the tracking event or checkpoint note",
        examples=["Package processed and sorted at Regional Hub"],
    )
    timestamp: Optional[datetime] = Field(
        default=None,
        description="Event timestamp in UTC. Defaults to current time if omitted.",
    )


class ShipmentTrackingEventResponse(BaseModel):
    """
    Response schema returning a tracking event record.
    """
    id: int = Field(..., description="Tracking event unique ID")
    shipment_id: int = Field(..., description="Associated shipment ID")
    event_type: str = Field(..., description="Type of tracking milestone")
    location: str = Field(..., description="Location of milestone")
    description: str = Field(..., description="Description of the event")
    timestamp: datetime = Field(..., description="Timestamp of the event")
    created_by_user_id: Optional[int] = Field(
        default=None,
        description="User who recorded the tracking event",
    )
    created_by: Optional[UserSummary] = Field(
        default=None,
        description="User details who recorded this event",
    )
    created_at: datetime = Field(..., description="System recorded timestamp")

    model_config = ConfigDict(from_attributes=True)


class LatestTrackingInfoResponse(BaseModel):
    """
    Combined real-time tracking summary for a shipment.
    Includes current status, last status transition, and latest physical event.
    """
    shipment_id: int = Field(..., description="Shipment ID")
    tracking_number: str = Field(..., description="Unique tracking identifier")
    current_status: ShipmentStatus = Field(..., description="Current operational state")
    destination_city: str = Field(..., description="Delivery destination city")
    destination_state: str = Field(..., description="Delivery destination state")
    delivered_at: Optional[datetime] = Field(default=None, description="Delivery completion timestamp")
    latest_status_history: Optional[ShipmentStatusHistoryResponse] = Field(
        default=None,
        description="Most recent status lifecycle transition",
    )
    latest_tracking_event: Optional[ShipmentTrackingEventResponse] = Field(
        default=None,
        description="Most recent physical tracking checkpoint or scan",
    )

    model_config = ConfigDict(from_attributes=True)
