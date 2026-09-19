"""
Shipment Endpoints
==================
API router for managing shipments, dispatches, tracking lookups,
state machine lifecycle transitions, audit status history, and physical tracking events.

Permissions:
- Create Shipment (POST): ADMIN, MANAGER
- Read Shipments (GET list, GET by ID, GET by tracking): All authenticated users
- Update Shipment (PUT/PATCH details, PATCH status): ADMIN, MANAGER
- Delete Shipment (DELETE soft-delete): ADMIN only
- Read History & Tracking (GET history, GET tracking, GET latest tracking): All authenticated users
- Add Tracking Event (POST tracking): ADMIN, MANAGER
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_roles
from app.models.user import User, UserRole
from app.models.shipment import ShipmentStatus
from app.schemas.shipment import (
    ShipmentCreate,
    ShipmentResponse,
    ShipmentUpdate,
    ShipmentStatusUpdate,
)
from app.schemas.tracking import (
    ShipmentStatusHistoryResponse,
    ShipmentTrackingEventCreate,
    ShipmentTrackingEventResponse,
    LatestTrackingInfoResponse,
)
from app.services.shipment_service import shipment_service
from app.services.tracking_service import tracking_service

router = APIRouter()


# ------------------------------------------------------------------------------
# Shipment Core Endpoints
# ------------------------------------------------------------------------------

@router.post(
    "",
    response_model=ShipmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new shipment",
    description="Registers a new shipment with origin, destination, and auto-generated tracking number. Accessible to ADMIN and MANAGER.",
)
def create_shipment(
    payload: ShipmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles([UserRole.ADMIN, UserRole.MANAGER])
    ),
) -> ShipmentResponse:
    """
    Creates a new shipment draft in CREATED status and records the initial status history.
    """
    return shipment_service.create_shipment(db, payload, current_user=current_user)


@router.get(
    "",
    response_model=List[ShipmentResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all shipments",
    description="Retrieves a paginated list of shipments with status and tracking filters. Accessible to all authenticated users.",
)
def get_all_shipments(
    status_filter: Optional[ShipmentStatus] = Query(
        None, alias="status", description="Filter by shipment lifecycle state"
    ),
    tracking_number: Optional[str] = Query(
        None, description="Search/filter by tracking number"
    ),
    origin_warehouse_id: Optional[int] = Query(
        None, description="Filter by origin warehouse ID"
    ),
    is_active: Optional[bool] = Query(
        None, description="Filter by active status (soft-delete flag)"
    ),
    skip: int = Query(0, ge=0, description="Records to skip for pagination"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[ShipmentResponse]:
    """
    Returns paginated list of shipments.
    """
    return shipment_service.list_shipments(
        db,
        skip=skip,
        limit=limit,
        status=status_filter,
        tracking_number=tracking_number,
        origin_warehouse_id=origin_warehouse_id,
        is_active=is_active,
    )


@router.get(
    "/tracking/{tracking_number}",
    response_model=ShipmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get shipment by tracking number",
    description="Retrieves shipment details using its unique human-readable tracking number. Accessible to all authenticated users.",
)
def get_shipment_by_tracking(
    tracking_number: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ShipmentResponse:
    """
    Returns single shipment by tracking number or raises 404 if not found.
    """
    return shipment_service.get_shipment_by_tracking(db, tracking_number)


@router.get(
    "/{shipment_id}",
    response_model=ShipmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get shipment by ID",
    description="Retrieves shipment details by primary key ID. Accessible to all authenticated users.",
)
def get_shipment_by_id(
    shipment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ShipmentResponse:
    """
    Returns single shipment by ID or raises 404 if not found.
    """
    return shipment_service.get_shipment(db, shipment_id)


@router.put(
    "/{shipment_id}",
    response_model=ShipmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Update shipment by ID",
    description="Modifies permitted shipment details. Blocked after delivery. Accessible to ADMIN and MANAGER.",
)
@router.patch(
    "/{shipment_id}",
    response_model=ShipmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Partially update shipment by ID",
    description="Partially modifies permitted shipment details. Blocked after delivery. Accessible to ADMIN and MANAGER.",
)
def update_shipment(
    shipment_id: int,
    payload: ShipmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles([UserRole.ADMIN, UserRole.MANAGER])
    ),
) -> ShipmentResponse:
    """
    Updates shipment information or raises 404 if not found.
    """
    return shipment_service.update_shipment(db, shipment_id, payload)


@router.patch(
    "/{shipment_id}/status",
    response_model=ShipmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Update shipment lifecycle status",
    description="Advances shipment state adhering strictly to the FlowGrid state machine. Records status transition history. Accessible to ADMIN and MANAGER.",
)
def update_shipment_status(
    shipment_id: int,
    payload: ShipmentStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles([UserRole.ADMIN, UserRole.MANAGER])
    ),
) -> ShipmentResponse:
    """
    Transitions shipment state or raises 400 if the transition is illegal.
    """
    return shipment_service.update_shipment_status(
        db, shipment_id, payload, current_user=current_user
    )


@router.delete(
    "/{shipment_id}",
    response_model=ShipmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete shipment (soft delete)",
    description="Soft-deletes a shipment by setting `is_active = False` to preserve audit history. Accessible to ADMIN only.",
)
def delete_shipment(
    shipment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
) -> ShipmentResponse:
    """
    Soft-deletes shipment or raises 404 if not found.
    """
    return shipment_service.delete_shipment(db, shipment_id)


# ------------------------------------------------------------------------------
# Shipment Status History & Physical Tracking Endpoints
# ------------------------------------------------------------------------------

@router.get(
    "/{shipment_id}/history",
    response_model=List[ShipmentStatusHistoryResponse],
    status_code=status.HTTP_200_OK,
    summary="Get shipment status history",
    description="Retrieves the chronological audit history of lifecycle status transitions for a shipment, newest first. Accessible to all authenticated users.",
)
def get_shipment_status_history(
    shipment_id: int,
    skip: int = Query(0, ge=0, description="Records to skip for pagination"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[ShipmentStatusHistoryResponse]:
    """
    Returns status change audit history records or raises 404 if the shipment does not exist.
    """
    return tracking_service.get_status_history(db, shipment_id, skip=skip, limit=limit)


@router.post(
    "/{shipment_id}/tracking",
    response_model=ShipmentTrackingEventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add shipment tracking event",
    description="Appends a physical checkpoint scan, arrival, or transit milestone to a shipment. Accessible to ADMIN and MANAGER.",
)
def add_tracking_event(
    shipment_id: int,
    payload: ShipmentTrackingEventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles([UserRole.ADMIN, UserRole.MANAGER])
    ),
) -> ShipmentTrackingEventResponse:
    """
    Records a new physical tracking event or raises 404 if the shipment does not exist.
    """
    return tracking_service.add_tracking_event(
        db, shipment_id, payload, current_user=current_user
    )


@router.get(
    "/{shipment_id}/tracking",
    response_model=List[ShipmentTrackingEventResponse],
    status_code=status.HTTP_200_OK,
    summary="Get shipment tracking events",
    description="Retrieves all physical tracking events and milestone checkpoints for a shipment, newest first. Accessible to all authenticated users.",
)
def get_shipment_tracking_events(
    shipment_id: int,
    skip: int = Query(0, ge=0, description="Records to skip for pagination"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[ShipmentTrackingEventResponse]:
    """
    Returns list of tracking events or raises 404 if the shipment does not exist.
    """
    return tracking_service.get_tracking_events(db, shipment_id, skip=skip, limit=limit)


@router.get(
    "/{shipment_id}/tracking/latest",
    response_model=LatestTrackingInfoResponse,
    status_code=status.HTTP_200_OK,
    summary="Get latest shipment tracking information",
    description="Retrieves real-time consolidated tracking information including current state, most recent status change, and latest physical tracking event. Accessible to all authenticated users.",
)
def get_latest_tracking_info(
    shipment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LatestTrackingInfoResponse:
    """
    Returns the latest status and tracking event for a shipment or raises 404 if not found.
    """
    return tracking_service.get_latest_tracking_info(db, shipment_id)
