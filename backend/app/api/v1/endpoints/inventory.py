"""
Inventory Endpoints
===================
API router for managing on-hand inventory levels and reorder thresholds across warehouses.

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
from app.schemas.inventory import (
    InventoryCreate,
    InventoryResponse,
    InventoryUpdate,
)
from app.services.inventory_service import inventory_service

router = APIRouter()


@router.post(
    "",
    response_model=InventoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create inventory record",
    description="Links a product to a warehouse with initial stock and threshold levels. Accessible to ADMIN and MANAGER.",
)
def create_inventory(
    payload: InventoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles([UserRole.ADMIN, UserRole.MANAGER])
    ),
) -> InventoryResponse:
    """
    Creates an inventory stock record. Validates active warehouse and product entities,
    and ensures no duplicate warehouse-product pairings exist.
    """
    return inventory_service.create_inventory(db, payload)


@router.get(
    "",
    response_model=List[InventoryResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all inventory records",
    description="Retrieves inventory stock balances. Supports filtering by warehouse_id and product_id with pagination. Accessible to all authenticated users.",
)
def get_all_inventory(
    warehouse_id: Optional[int] = Query(None, description="Filter by warehouse ID"),
    product_id: Optional[int] = Query(None, description="Filter by product ID"),
    skip: int = Query(0, ge=0, description="Records to skip for pagination"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[InventoryResponse]:
    """
    Returns paginated inventory stock list.
    """
    return inventory_service.list_inventory(
        db,
        skip=skip,
        limit=limit,
        warehouse_id=warehouse_id,
        product_id=product_id,
    )


@router.get(
    "/{inventory_id}",
    response_model=InventoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get inventory record by ID",
    description="Retrieves a specific inventory record by ID. Accessible to all authenticated users.",
)
def get_inventory_by_id(
    inventory_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InventoryResponse:
    """
    Returns single inventory record by ID or raises 404 if not found.
    """
    return inventory_service.get_inventory(db, inventory_id)


@router.put(
    "/{inventory_id}",
    response_model=InventoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Update inventory by ID",
    description="Modifies quantity and/or reorder level of an inventory record. Accessible to ADMIN and MANAGER.",
)
@router.patch(
    "/{inventory_id}",
    response_model=InventoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Partially update inventory by ID",
    description="Partially modifies quantity and/or reorder level. Accessible to ADMIN and MANAGER.",
)
def update_inventory(
    inventory_id: int,
    payload: InventoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles([UserRole.ADMIN, UserRole.MANAGER])
    ),
) -> InventoryResponse:
    """
    Updates inventory stock balance or raises 404 if not found.
    """
    return inventory_service.update_inventory(db, inventory_id, payload)


@router.delete(
    "/{inventory_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete inventory record",
    description="Deletes an inventory record. Accessible to ADMIN role only.",
)
def delete_inventory(
    inventory_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
) -> Dict[str, Any]:
    """
    Deletes inventory record or raises 404 if not found.
    """
    return inventory_service.delete_inventory(db, inventory_id)
