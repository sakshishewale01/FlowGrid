"""
Analytics and Dashboard Endpoints
=================================
API router providing high-performance operational metrics, throughput analytics,
inventory alerts, and fleet corridor performance.

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
)
from app.services.analytics_service import analytics_service

router = APIRouter()


@router.get(
    "/overview",
    response_model=OverviewAnalyticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get overview statistics",
    description="Retrieves high-level operational KPIs spanning shipments, facilities, products, drivers, and routes. Accessible to all authenticated users.",
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
    description="Retrieves shipment lifecycle distribution, daily throughput volume, delivery completion rates, and exception counts. Accessible to all authenticated users.",
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
    Returns shipment status distribution and chronological volume.
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
    description="Retrieves network-wide warehouse counts (active vs inactive) and facility capacity profiles. Accessible to all authenticated users.",
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
