"""
Driver Endpoints
================
API router for managing field logistics drivers and user account linkages.

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
from app.schemas.driver import (
    DriverCreate,
    DriverResponse,
    DriverUpdate,
)
from app.services.driver_service import driver_service

router = APIRouter()


@router.post(
    "",
    response_model=DriverResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create driver profile",
    description="Registers a new driver profile linked to an existing active user account. Accessible to ADMIN and MANAGER.",
)
def create_driver(
    payload: DriverCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles([UserRole.ADMIN, UserRole.MANAGER])
    ),
) -> DriverResponse:
    """
    Creates a driver profile with validated license uniqueness.
    """
    return driver_service.create_driver(db, payload)


@router.get(
    "",
    response_model=List[DriverResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all drivers",
    description="Retrieves a paginated list of driver profiles. Supports filtering by availability status and active user status. Accessible to all authenticated users.",
)
def get_all_drivers(
    availability_status: Optional[str] = Query(
        None, description="Filter by availability status (e.g. AVAILABLE, ON_DUTY, IN_TRANSIT, OFF_DUTY)"
    ),
    is_active: Optional[bool] = Query(
        None, description="Filter by active status of the linked user account"
    ),
    skip: int = Query(0, ge=0, description="Records to skip for pagination"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[DriverResponse]:
    """
    Returns paginated list of drivers.
    """
    return driver_service.list_drivers(
        db,
        skip=skip,
        limit=limit,
        availability_status=availability_status,
        is_active=is_active,
    )


@router.get(
    "/{driver_id}",
    response_model=DriverResponse,
    status_code=status.HTTP_200_OK,
    summary="Get driver by ID",
    description="Retrieves driver profile details by primary key ID. Accessible to all authenticated users.",
)
def get_driver_by_id(
    driver_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DriverResponse:
    """
    Returns single driver profile by ID or raises 404 if not found.
    """
    return driver_service.get_driver(db, driver_id)


@router.put(
    "/{driver_id}",
    response_model=DriverResponse,
    status_code=status.HTTP_200_OK,
    summary="Update driver by ID",
    description="Modifies attributes of an existing driver profile. Accessible to ADMIN and MANAGER.",
)
@router.patch(
    "/{driver_id}",
    response_model=DriverResponse,
    status_code=status.HTTP_200_OK,
    summary="Partially update driver by ID",
    description="Partially modifies attributes of an existing driver profile. Accessible to ADMIN and MANAGER.",
)
def update_driver(
    driver_id: int,
    payload: DriverUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles([UserRole.ADMIN, UserRole.MANAGER])
    ),
) -> DriverResponse:
    """
    Updates driver profile attributes or raises 404 if not found.
    """
    return driver_service.update_driver(db, driver_id, payload)


@router.delete(
    "/{driver_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete driver profile",
    description="Permanently deletes a driver profile record. Accessible to ADMIN role only.",
)
def delete_driver(
    driver_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
) -> Dict[str, Any]:
    """
    Deletes driver profile or raises 404 if not found.
    """
    return driver_service.delete_driver(db, driver_id)
