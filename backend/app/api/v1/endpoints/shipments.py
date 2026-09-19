"""
Shipment Endpoints
==================
API router for managing shipments, dispatches, tracking lookups, and state machine lifecycle transitions.

Permissions:
- Create (POST): ADMIN, MANAGER
- Read (GET list, GET by ID, GET by tracking): All authenticated users
- Update (PUT/PATCH details, PATCH status): ADMIN, MANAGER
- Delete (DELETE soft-delete): ADMIN only
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
from app.services.shipment_service import shipment_service

router = APIRouter()


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
    Creates a new shipment draft in CREATED status.
    """
    return shipment_service.create_shipment(db, payload)


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
    description="Advances shipment state adhering strictly to the FlowGrid state machine. Accessible to ADMIN and MANAGER.",
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
    return shipment_service.update_shipment_status(db, shipment_id, payload)


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
