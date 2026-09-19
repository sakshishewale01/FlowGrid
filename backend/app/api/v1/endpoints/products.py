"""
Product Endpoints
=================
API router for managing items in the commercial product catalog.

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
from app.schemas.product import (
    ProductCreate,
    ProductResponse,
    ProductUpdate,
)
from app.services.product_service import product_service

router = APIRouter()


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new product",
    description="Registers a new item in the product catalog. Accessible to ADMIN and MANAGER roles.",
)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles([UserRole.ADMIN, UserRole.MANAGER])
    ),
) -> ProductResponse:
    """
    Creates a new product item in the FlowGrid catalog.
    Validates unique SKU and non-negative unit price.
    """
    return product_service.create_product(db, payload)


@router.get(
    "",
    response_model=List[ProductResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all products",
    description="Retrieves a paginated list of catalog products. Accessible to all authenticated users.",
)
def get_all_products(
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(100, ge=1, le=1000, description="Max number of records to return"),
    is_active: Optional[bool] = Query(
        None,
        description="Filter by active status (true for active, false for inactive, null for all)",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[ProductResponse]:
    """
    Returns paginated list of catalog products.
    """
    return product_service.list_products(
        db,
        skip=skip,
        limit=limit,
        is_active=is_active,
    )


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    summary="Get product by ID",
    description="Retrieves details for a specific catalog product. Accessible to all authenticated users.",
)
def get_product_by_id(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProductResponse:
    """
    Returns single product by ID or raises 404 if not found.
    """
    return product_service.get_product(db, product_id)


@router.put(
    "/{product_id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    summary="Update product by ID",
    description="Modifies attributes of an existing product. Accessible to ADMIN and MANAGER roles.",
)
@router.patch(
    "/{product_id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    summary="Partially update product by ID",
    description="Partially modifies attributes of an existing product. Accessible to ADMIN and MANAGER roles.",
)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles([UserRole.ADMIN, UserRole.MANAGER])
    ),
) -> ProductResponse:
    """
    Updates product fields or raises 404 if not found.
    """
    return product_service.update_product(db, product_id, payload)


@router.delete(
    "/{product_id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete product (soft delete)",
    description="Soft-deletes a product by setting `is_active = False`. Accessible to ADMIN role only.",
)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
) -> ProductResponse:
    """
    Soft-deletes product by setting `is_active = False` or raises 404 if not found.
    """
    return product_service.delete_product(db, product_id)
