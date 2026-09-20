"""
Route Endpoints
===============
API router for managing transportation corridors, multi-stop routes,
and assigning shipments.

Permissions:
- Create Route (POST /): ADMIN, MANAGER
- Read Routes (GET /, GET /{id}): All authenticated users (ADMIN, MANAGER, DRIVER, VIEWER)
- Update Route (PUT/PATCH /{id}): ADMIN, MANAGER
- Delete Route (DELETE /{id}): ADMIN only (Soft deletion)
- Assign Shipments (POST /{id}/shipments): ADMIN, MANAGER
- Read Route Shipments (GET /{id}/shipments): All authenticated users
"""

from typing import List, Optional, Union
from fastapi import APIRouter, Depends, Query, Body, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_roles
from app.models.user import User, UserRole
from app.schemas.route import (
    RouteCreate,
    RouteUpdate,
    RouteResponse,
    RouteShipmentAssign,
)
from app.schemas.shipment import ShipmentResponse
from app.services.route_service import route_service

router = APIRouter()


@router.post(
    "",
    response_model=RouteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create route",
    description="Creates a new transit corridor or delivery route. Accessible to ADMIN and MANAGER.",
)
def create_route(
    payload: RouteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles([UserRole.ADMIN, UserRole.MANAGER])
    ),
) -> RouteResponse:
    """
    Creates a new logistics route record with validated origin, destination, and metrics.
    """
    return route_service.create_route(db, payload)


@router.get(
    "",
    response_model=List[RouteResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all routes",
    description="Retrieves a paginated list of routes with optional status and active filtering. Accessible to all authenticated users.",
)
def get_all_routes(
    skip: int = Query(0, ge=0, description="Records to skip for pagination"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    status: Optional[str] = Query(None, description="Filter by operational status (e.g., ACTIVE, PLANNED, COMPLETED)"),
    is_active: Optional[bool] = Query(None, description="Filter by active operational status"),
    search: Optional[str] = Query(None, description="Search by route name, origin, or destination"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[RouteResponse]:
    """
    Returns list of routes matching pagination and filtering parameters.
    """
    return route_service.list_routes(
        db,
        skip=skip,
        limit=limit,
        status_filter=status,
        is_active=is_active,
        search=search,
    )


@router.get(
    "/{route_id}",
    response_model=RouteResponse,
    status_code=status.HTTP_200_OK,
    summary="Get route by ID",
    description="Retrieves a specific route by its primary key ID. Accessible to all authenticated users.",
)
def get_route_by_id(
    route_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RouteResponse:
    """
    Returns single route by ID or raises 404 if not found.
    """
    return route_service.get_route(db, route_id)


@router.put(
    "/{route_id}",
    response_model=RouteResponse,
    status_code=status.HTTP_200_OK,
    summary="Update route (PUT)",
    description="Updates route details. Accessible to ADMIN and MANAGER.",
)
@router.patch(
    "/{route_id}",
    response_model=RouteResponse,
    status_code=status.HTTP_200_OK,
    summary="Update route (PATCH)",
    description="Partially updates route details. Accessible to ADMIN and MANAGER.",
)
def update_route(
    route_id: int,
    payload: RouteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles([UserRole.ADMIN, UserRole.MANAGER])
    ),
) -> RouteResponse:
    """
    Updates route information or raises 404 if not found.
    """
    return route_service.update_route(db, route_id, payload)


@router.delete(
    "/{route_id}",
    response_model=RouteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete route (soft delete)",
    description="Soft-deletes a route by setting `is_active = False`. Accessible to ADMIN only.",
)
def delete_route(
    route_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
) -> RouteResponse:
    """
    Soft-deletes route by setting is_active = False or raises 404 if not found.
    """
    return route_service.delete_route(db, route_id)


@router.post(
    "/{route_id}/shipments",
    response_model=List[ShipmentResponse],
    status_code=status.HTTP_200_OK,
    summary="Assign shipments to route",
    description="Allocates one or more shipments to a route. Accessible to ADMIN and MANAGER.",
)
def assign_shipments_to_route(
    route_id: int,
    payload: Union[RouteShipmentAssign, List[int]] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles([UserRole.ADMIN, UserRole.MANAGER])
    ),
) -> List[ShipmentResponse]:
    """
    Assigns shipments to the specified route transactionally.
    Validates route and shipments exist, prevents duplicate allocations,
    and returns the assigned shipments.
    """
    if isinstance(payload, list):
        shipment_ids = payload
    else:
        shipment_ids = payload.get_ids()

    return route_service.assign_shipments_to_route(
        db,
        route_id=route_id,
        shipment_ids=shipment_ids,
        current_user=current_user,
    )


@router.post(
    "/{route_id}/shipments/{shipment_id}",
    response_model=List[ShipmentResponse],
    status_code=status.HTTP_200_OK,
    summary="Assign single shipment to route by path parameter",
    description="Convenience endpoint to assign a single shipment to a route. Accessible to ADMIN and MANAGER.",
)
def assign_single_shipment_to_route(
    route_id: int,
    shipment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles([UserRole.ADMIN, UserRole.MANAGER])
    ),
) -> List[ShipmentResponse]:
    """
    Assigns a single shipment to the route.
    """
    return route_service.assign_shipments_to_route(
        db,
        route_id=route_id,
        shipment_ids=[shipment_id],
        current_user=current_user,
    )


@router.get(
    "/{route_id}/shipments",
    response_model=List[ShipmentResponse],
    status_code=status.HTTP_200_OK,
    summary="Get route shipments",
    description="Retrieves all shipments assigned to a specific route. Accessible to all authenticated users.",
)
def get_route_shipments(
    route_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[ShipmentResponse]:
    """
    Returns list of shipments assigned to the route or raises 404 if the route is not found.
    """
    return route_service.get_route_shipments(db, route_id)
