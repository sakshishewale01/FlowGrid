"""
Vehicle Endpoints
=================
API router for managing transport fleet units and vehicles.

Permissions:
- Create (POST): ADMIN, MANAGER
- Read (GET list, GET by ID): All authenticated users (ADMIN, MANAGER, DRIVER, VIEWER)
- Update (PUT/PATCH): ADMIN, MANAGER
- Delete (DELETE): ADMIN only
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_roles
from app.models.user import User, UserRole
from app.schemas.vehicle import (
    VehicleCreate,
    VehicleResponse,
    VehicleUpdate,
)
from app.services.vehicle_service import vehicle_service

router = APIRouter()


@router.post(
    "",
    response_model=VehicleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create fleet vehicle",
    description="Registers a new transport vehicle with unique registration number and capacity. Accessible to ADMIN and MANAGER.",
)
def create_vehicle(
    payload: VehicleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles([UserRole.ADMIN, UserRole.MANAGER])
    ),
) -> VehicleResponse:
    """
    Registers a new vehicle in the logistics network.
    """
    return vehicle_service.create_vehicle(db, payload)


@router.get(
    "",
    response_model=List[VehicleResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all vehicles",
    description="Retrieves a paginated list of fleet vehicles. Supports filtering by status or active status. Accessible to all authenticated users.",
)
def get_all_vehicles(
    status_filter: Optional[str] = Query(
        None,
        alias="status",
        description="Filter by status (e.g. AVAILABLE, IN_USE, MAINTENANCE, DECOMMISSIONED)",
    ),
    is_active: Optional[bool] = Query(
        None,
        description="Filter by active status (true for non-decommissioned, false for decommissioned)",
    ),
    skip: int = Query(0, ge=0, description="Records to skip for pagination"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[VehicleResponse]:
    """
    Returns paginated list of vehicles.
    """
    return vehicle_service.list_vehicles(
        db,
        skip=skip,
        limit=limit,
        status=status_filter,
        is_active=is_active,
    )


@router.get(
    "/{vehicle_id}",
    response_model=VehicleResponse,
    status_code=status.HTTP_200_OK,
    summary="Get vehicle by ID",
    description="Retrieves specific vehicle details by primary key ID. Accessible to all authenticated users.",
)
def get_vehicle_by_id(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> VehicleResponse:
    """
    Returns single vehicle by ID or raises 404 if not found.
    """
    return vehicle_service.get_vehicle(db, vehicle_id)


@router.put(
    "/{vehicle_id}",
    response_model=VehicleResponse,
    status_code=status.HTTP_200_OK,
    summary="Update vehicle by ID",
    description="Modifies attributes of an existing vehicle. Accessible to ADMIN and MANAGER.",
)
@router.patch(
    "/{vehicle_id}",
    response_model=VehicleResponse,
    status_code=status.HTTP_200_OK,
    summary="Partially update vehicle by ID",
    description="Partially modifies attributes of an existing vehicle. Accessible to ADMIN and MANAGER.",
)
def update_vehicle(
    vehicle_id: int,
    payload: VehicleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles([UserRole.ADMIN, UserRole.MANAGER])
    ),
) -> VehicleResponse:
    """
    Updates vehicle attributes or raises 404 if not found.
    """
    return vehicle_service.update_vehicle(db, vehicle_id, payload)


@router.delete(
    "/{vehicle_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete vehicle",
    description="Permanently deletes a vehicle entity from the fleet database. Accessible to ADMIN role only.",
)
def delete_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
) -> Dict[str, Any]:
    """
    Deletes vehicle or raises 404 if not found.
    """
    return vehicle_service.delete_vehicle(db, vehicle_id)
