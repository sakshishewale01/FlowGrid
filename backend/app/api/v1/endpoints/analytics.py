"""
Analytics and Dashboard Endpoints
=================================
API router providing high-performance operational metrics, throughput analytics,
inventory alerts, fleet corridor performance, driver availability, and vehicle fleet utilization.

Permissions:
- All authenticated roles (ADMIN, MANAGER, DRIVER, VIEWER) can read analytics data.
- Unauthenticated requests are rejected with HTTP 401 Unauthorized.
"""

from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.analytics import (
    OverviewAnalyticsResponse,
    ShipmentAnalyticsResponse,
    InventoryAnalyticsResponse,
    WarehouseAnalyticsResponse,
    RouteAnalyticsResponse,
    DriverAnalyticsResponse,
    VehicleAnalyticsResponse,
)
from app.services.analytics_service import analytics_service

router = APIRouter()


@router.get(
    "/overview",
    response_model=OverviewAnalyticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get overview statistics",
    description="Retrieves high-level operational KPIs spanning shipments, facilities, products, drivers, fleet vehicles, and routes. Accessible to all authenticated users.",
)
def get_overview_statistics(
    start_date: Optional[date] = Query(
        None,
        description="Optional start date filter (inclusive, YYYY-MM-DD)",
        examples=["2026-09-01"],
    ),
    end_date: Optional[date] = Query(
        None,
        description="Optional end date filter (inclusive, YYYY-MM-DD)",
        examples=["2026-09-30"],
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OverviewAnalyticsResponse:
    """
    Returns consolidated dashboard overview metrics.
    """
    return analytics_service.get_overview(
        db, start_date=start_date, end_date=end_date
    )


@router.get(
    "/shipments",
    response_model=ShipmentAnalyticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get shipment analytics",
    description="Retrieves shipment lifecycle distribution, daily throughput volume, delivery completion rates, on-time performance, and exception counts. Accessible to all authenticated users.",
)
def get_shipment_analytics(
    start_date: Optional[date] = Query(
        None,
        description="Optional start date filter (inclusive, YYYY-MM-DD)",
        examples=["2026-09-01"],
    ),
    end_date: Optional[date] = Query(
        None,
        description="Optional end date filter (inclusive, YYYY-MM-DD)",
        examples=["2026-09-30"],
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ShipmentAnalyticsResponse:
    """
    Returns shipment status distribution, chronological volume, and delivery performance.
    """
    return analytics_service.get_shipments(
        db, start_date=start_date, end_date=end_date
    )


@router.get(
    "/inventory",
    response_model=InventoryAnalyticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get inventory analytics",
    description="Retrieves gross inventory balances, safety stock threshold violations, and facility-level allocation breakdowns. Accessible to all authenticated users.",
)
def get_inventory_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InventoryAnalyticsResponse:
    """
    Returns inventory balances and low-stock product warnings.
    """
    return analytics_service.get_inventory(db)


@router.get(
    "/warehouses",
    response_model=WarehouseAnalyticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get warehouse analytics",
    description="Retrieves network-wide warehouse counts (active vs inactive), capacity utilization, and facility profiles. Accessible to all authenticated users.",
)
def get_warehouse_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WarehouseAnalyticsResponse:
    """
    Returns warehouse facility summaries and operational status counts.
    """
    return analytics_service.get_warehouses(db)


@router.get(
    "/routes",
    response_model=RouteAnalyticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get route analytics",
    description="Retrieves freight corridor status distributions, active vs completed counts, and shipment allocation density. Accessible to all authenticated users.",
)
def get_route_analytics(
    start_date: Optional[date] = Query(
        None,
        description="Optional start date filter (inclusive, YYYY-MM-DD)",
        examples=["2026-09-01"],
    ),
    end_date: Optional[date] = Query(
        None,
        description="Optional end date filter (inclusive, YYYY-MM-DD)",
        examples=["2026-09-30"],
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RouteAnalyticsResponse:
    """
    Returns route analytics and corridor utilization summaries.
    """
    return analytics_service.get_routes(
        db, start_date=start_date, end_date=end_date
    )


@router.get(
    "/drivers",
    response_model=DriverAnalyticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get driver analytics",
    description="Retrieves driver workforce status distribution, active user account counts, driver utilization rates, and assigned shipment workload. Accessible to all authenticated users.",
)
def get_driver_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DriverAnalyticsResponse:
    """
    Returns fleet driver workforce and availability metrics.
    """
    return analytics_service.get_drivers(db)


@router.get(
    "/vehicles",
    response_model=VehicleAnalyticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get vehicle analytics",
    description="Retrieves fleet vehicle status distribution, vehicle type breakdown, total carrying capacity, and utilization rates. Accessible to all authenticated users.",
)
def get_vehicle_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> VehicleAnalyticsResponse:
    """
    Returns fleet vehicle utilization, capacity, and status distribution.
    """
    return analytics_service.get_vehicles(db)
