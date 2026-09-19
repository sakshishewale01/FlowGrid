"""
Warehouse Endpoints
===================
API router for managing physical warehouses, fulfillment hubs, and distribution centers.

Permissions:
- Create (POST): ADMIN, MANAGER
- Read (GET list, GET by ID): All authenticated users (ADMIN, MANAGER, DRIVER, VIEWER)
- Update (PUT/PATCH): ADMIN, MANAGER
- Delete (DELETE soft-delete): ADMIN only
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_roles
from app.models.user import User, UserRole
from app.schemas.warehouse import (
    WarehouseCreate,
    WarehouseResponse,
    WarehouseUpdate,
)
from app.services.warehouse_service import warehouse_service

router = APIRouter()


@router.post(
    "",
    response_model=WarehouseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new warehouse",
    description="Registers a new warehouse facility. Accessible to ADMIN and MANAGER roles.",
)
def create_warehouse(
    payload: WarehouseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles([UserRole.ADMIN, UserRole.MANAGER])
    ),
) -> WarehouseResponse:
    """
    Creates a new warehouse facility in FlowGrid.
    """
    return warehouse_service.create_warehouse(db, payload)


@router.get(
    "",
    response_model=List[WarehouseResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all warehouses",
    description="Retrieves a list of warehouses. Accessible to all authenticated users.",
)
def get_all_warehouses(
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(100, ge=1, le=1000, description="Max number of records to return"),
    is_active: Optional[bool] = Query(
        None,
        description="Filter by active status (true for active, false for inactive, null for all)",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[WarehouseResponse]:
    """
    Returns paginated list of warehouses.
    """
    return warehouse_service.list_warehouses(
        db,
        skip=skip,
        limit=limit,
        is_active=is_active,
    )


@router.get(
    "/{warehouse_id}",
    response_model=WarehouseResponse,
    status_code=status.HTTP_200_OK,
    summary="Get warehouse by ID",
    description="Retrieves details for a specific warehouse by its ID. Accessible to all authenticated users.",
)
def get_warehouse_by_id(
    warehouse_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WarehouseResponse:
    """
    Returns single warehouse by ID or raises 404 if not found.
    """
    return warehouse_service.get_warehouse(db, warehouse_id)


@router.put(
    "/{warehouse_id}",
    response_model=WarehouseResponse,
    status_code=status.HTTP_200_OK,
    summary="Update warehouse by ID",
    description="Modifies attributes of an existing warehouse. Accessible to ADMIN and MANAGER roles.",
)
@router.patch(
    "/{warehouse_id}",
    response_model=WarehouseResponse,
    status_code=status.HTTP_200_OK,
    summary="Partially update warehouse by ID",
    description="Partially modifies attributes of an existing warehouse. Accessible to ADMIN and MANAGER roles.",
)
def update_warehouse(
    warehouse_id: int,
    payload: WarehouseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles([UserRole.ADMIN, UserRole.MANAGER])
    ),
) -> WarehouseResponse:
    """
    Updates warehouse fields or raises 404 if not found.
    """
    return warehouse_service.update_warehouse(db, warehouse_id, payload)


@router.delete(
    "/{warehouse_id}",
    response_model=WarehouseResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete warehouse (soft delete)",
    description="Soft-deletes a warehouse by setting `is_active = False`. Accessible to ADMIN role only.",
)
def delete_warehouse(
    warehouse_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
) -> WarehouseResponse:
    """
    Soft-deletes warehouse by setting `is_active = False` or raises 404 if not found.
    """
    return warehouse_service.delete_warehouse(db, warehouse_id)
