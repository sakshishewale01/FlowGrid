"""
Analytics Service
=================
Business logic layer managing dashboard KPIs, date range validations,
and coordination with the Analytics Repository.
"""

from datetime import date, datetime, time, timezone
from typing import Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.analytics_repository import analytics_repository
from app.schemas.analytics import (
    OverviewAnalyticsResponse,
    ShipmentAnalyticsResponse,
    InventoryAnalyticsResponse,
    WarehouseAnalyticsResponse,
    RouteAnalyticsResponse,
    DriverAnalyticsResponse,
    VehicleAnalyticsResponse,
)


class AnalyticsService:
    """
    Business service coordinating analytical reporting, date range validation,
    and structured aggregation responses.
    """

    def __init__(self, repository=analytics_repository):
        self.repository = repository

    @staticmethod
    def validate_and_convert_dates(
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Tuple[Optional[datetime], Optional[datetime]]:
        """
        Validates date parameters and converts calendar dates into UTC timezone-aware
        datetime boundaries.

        Raises:
            HTTPException (400 BAD REQUEST): If start_date > end_date.
        """
        if start_date is not None and end_date is not None:
            if start_date > end_date:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="start_date cannot be after end_date",
                )

        start_dt: Optional[datetime] = None
        end_dt: Optional[datetime] = None

        if start_date is not None:
            start_dt = datetime.combine(start_date, time.min).replace(
                tzinfo=timezone.utc
            )

        if end_date is not None:
            end_dt = datetime.combine(end_date, time.max).replace(
                tzinfo=timezone.utc
            )

        return start_dt, end_dt

    def get_overview(
        self,
        db: Session,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> OverviewAnalyticsResponse:
        """
        Calculates executive KPIs across all logistics modules.
        """
        start_dt, end_dt = self.validate_and_convert_dates(start_date, end_date)
        raw_data = self.repository.get_overview_statistics(
            db, start_datetime=start_dt, end_datetime=end_dt
        )
        return OverviewAnalyticsResponse(**raw_data)

    def get_shipments(
        self,
        db: Session,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> ShipmentAnalyticsResponse:
        """
        Aggregates shipment lifecycle metrics, status breakdown, and daily throughput.
        """
        start_dt, end_dt = self.validate_and_convert_dates(start_date, end_date)
        raw_data = self.repository.get_shipment_analytics(
            db, start_datetime=start_dt, end_datetime=end_dt
        )
        return ShipmentAnalyticsResponse(**raw_data)

    def get_inventory(self, db: Session) -> InventoryAnalyticsResponse:
        """
        Calculates global stock balances, safety threshold violations, and facility allocations.
        """
        raw_data = self.repository.get_inventory_analytics(db)
        return InventoryAnalyticsResponse(**raw_data)

    def get_warehouses(self, db: Session) -> WarehouseAnalyticsResponse:
        """
        Calculates active vs inactive warehouse counts and facility-level capacity utilization.
        """
        raw_data = self.repository.get_warehouse_analytics(db)
        return WarehouseAnalyticsResponse(**raw_data)

    def get_routes(
        self,
        db: Session,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> RouteAnalyticsResponse:
        """
        Aggregates route status counts and assigned shipment density.
        """
        start_dt, end_dt = self.validate_and_convert_dates(start_date, end_date)
        raw_data = self.repository.get_route_analytics(
            db, start_datetime=start_dt, end_datetime=end_dt
        )
        return RouteAnalyticsResponse(**raw_data)

    def get_drivers(self, db: Session) -> DriverAnalyticsResponse:
        """
        Calculates driver availability distribution, active user accounts, and utilization.
        """
        raw_data = self.repository.get_driver_analytics(db)
        return DriverAnalyticsResponse(**raw_data)

    def get_vehicles(self, db: Session) -> VehicleAnalyticsResponse:
        """
        Calculates fleet vehicle status distribution, carrying capacity, and utilization.
        """
        raw_data = self.repository.get_vehicle_analytics(db)
        return VehicleAnalyticsResponse(**raw_data)


analytics_service = AnalyticsService()
