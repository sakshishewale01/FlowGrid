"""
Analytics Repository
====================
Encapsulates high-performance SQL aggregation queries and group-by calculations
across Shipments, Inventory, Warehouses, Products, Drivers, and Routes.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy import select, func, cast, Date, case, distinct
from sqlalchemy.orm import Session

from app.models.shipment import Shipment, ShipmentStatus
from app.models.warehouse import Warehouse
from app.models.product import Product
from app.models.inventory import Inventory
from app.models.driver import Driver
from app.models.route import Route, RouteStatus, RouteShipment


class AnalyticsRepository:
    """
    Data access layer for analytical aggregations and KPI calculations.
    Optimized to execute database-level aggregations and avoid full dataset loads.
    """

    @staticmethod
    def get_overview_statistics(
        db: Session,
        start_datetime: Optional[datetime] = None,
        end_datetime: Optional[datetime] = None,
    ) -> Dict[str, int]:
        """
        Calculates executive KPIs across all logistics modules.
        """
        # 1. Shipment metrics with optional time window
        shipment_stmt = select(
            func.count(Shipment.id).label("total"),
            func.coalesce(
                func.sum(
                    case(
                        (
                            Shipment.is_active.is_(True)
                            & Shipment.status.in_(
                                [
                                    ShipmentStatus.CREATED,
                                    ShipmentStatus.CONFIRMED,
                                    ShipmentStatus.ASSIGNED,
                                    ShipmentStatus.PICKED_UP,
                                    ShipmentStatus.IN_TRANSIT,
                                    ShipmentStatus.OUT_FOR_DELIVERY,
                                ]
                            ),
                            1,
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label("active"),
            func.coalesce(
                func.sum(
                    case(
                        (Shipment.status == ShipmentStatus.DELIVERED, 1),
                        else_=0,
                    )
                ),
                0,
            ).label("delivered"),
            func.coalesce(
                func.sum(
                    case(
                        (
                            Shipment.status.in_(
                                [ShipmentStatus.FAILED, ShipmentStatus.RETURNED]
                            ),
                            1,
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label("delayed_or_failed"),
        )

        if start_datetime is not None:
            shipment_stmt = shipment_stmt.where(Shipment.created_at >= start_datetime)
        if end_datetime is not None:
            shipment_stmt = shipment_stmt.where(Shipment.created_at <= end_datetime)

        shipment_row = db.execute(shipment_stmt).one()

        # 2. Total Warehouses
        total_warehouses = db.scalar(select(func.count(Warehouse.id))) or 0

        # 3. Total Products
        total_products = db.scalar(select(func.count(Product.id))) or 0

        # 4. Total Drivers
        total_drivers = db.scalar(select(func.count(Driver.id))) or 0

        # 5. Active Routes
        active_routes = (
            db.scalar(
                select(func.count(Route.id)).where(
                    Route.is_active.is_(True),
                    Route.status == RouteStatus.ACTIVE,
                )
            )
            or 0
        )

        return {
            "total_shipments": int(shipment_row.total or 0),
            "active_shipments": int(shipment_row.active or 0),
            "delivered_shipments": int(shipment_row.delivered or 0),
            "delayed_or_failed_shipments": int(shipment_row.delayed_or_failed or 0),
            "total_warehouses": total_warehouses,
            "total_products": total_products,
            "total_drivers": total_drivers,
            "active_routes": active_routes,
        }

    @staticmethod
    def get_shipment_analytics(
        db: Session,
        start_datetime: Optional[datetime] = None,
        end_datetime: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Aggregates shipment distribution by lifecycle status and daily creation date.
        """
        # Status distribution query
        status_stmt = select(
            Shipment.status,
            func.count(Shipment.id).label("count"),
        ).group_by(Shipment.status)

        if start_datetime is not None:
            status_stmt = status_stmt.where(Shipment.created_at >= start_datetime)
        if end_datetime is not None:
            status_stmt = status_stmt.where(Shipment.created_at <= end_datetime)

        status_rows = db.execute(status_stmt).all()

        # Initialize all known statuses to 0 for consistent JSON response
        by_status: Dict[str, int] = {s.value: 0 for s in ShipmentStatus}
        total_shipments = 0
        for row in status_rows:
            st = row[0].value if hasattr(row[0], "value") else str(row[0])
            count = int(row[1])
            by_status[st] = count
            total_shipments += count

        # Date distribution query
        date_col = func.date(Shipment.created_at)
        date_stmt = (
            select(
                date_col.label("day"),
                func.count(Shipment.id).label("count"),
            )
            .group_by(date_col)
            .order_by(date_col.asc())
        )

        if start_datetime is not None:
            date_stmt = date_stmt.where(Shipment.created_at >= start_datetime)
        if end_datetime is not None:
            date_stmt = date_stmt.where(Shipment.created_at <= end_datetime)

        date_rows = db.execute(date_stmt).all()
        by_date = [
            {"date": str(row.day), "count": int(row.count)}
            for row in date_rows
            if row.day is not None
        ]

        delivered_count = by_status.get(ShipmentStatus.DELIVERED.value, 0)
        cancelled_count = by_status.get(ShipmentStatus.CANCELLED.value, 0)
        returned_count = by_status.get(ShipmentStatus.RETURNED.value, 0)

        completion_rate = (
            round((delivered_count / total_shipments) * 100.0, 2)
            if total_shipments > 0
            else 0.0
        )

        return {
            "total_shipments": total_shipments,
            "by_status": by_status,
            "by_date": by_date,
            "delivery_completion_rate": completion_rate,
            "cancelled_shipments": cancelled_count,
            "returned_shipments": returned_count,
        }

    @staticmethod
    def get_inventory_analytics(db: Session) -> Dict[str, Any]:
        """
        Calculates global stock balances, safety thresholds, and warehouse breakdowns.
        """
        # Gross metrics
        gross_stmt = select(
            func.count(Inventory.id).label("total_records"),
            func.coalesce(func.sum(Inventory.quantity), 0).label("total_qty"),
            func.coalesce(
                func.sum(
                    case(
                        (Inventory.quantity <= Inventory.reorder_level, 1),
                        else_=0,
                    )
                ),
                0,
            ).label("low_stock_count"),
        )
        gross_row = db.execute(gross_stmt).one()

        # Itemized low stock warnings
        low_stock_stmt = (
            select(
                Product.id.label("product_id"),
                Product.name.label("product_name"),
                Product.sku.label("sku"),
                Warehouse.id.label("warehouse_id"),
                Warehouse.name.label("warehouse_name"),
                Inventory.quantity.label("quantity"),
                Inventory.reorder_level.label("reorder_level"),
            )
            .join(Product, Product.id == Inventory.product_id)
            .join(Warehouse, Warehouse.id == Inventory.warehouse_id)
            .where(Inventory.quantity <= Inventory.reorder_level)
            .order_by(Inventory.quantity.asc(), Product.name.asc())
        )
        low_stock_rows = db.execute(low_stock_stmt).all()
        low_stock_products = [
            {
                "product_id": row.product_id,
                "product_name": row.product_name,
                "sku": row.sku,
                "warehouse_id": row.warehouse_id,
                "warehouse_name": row.warehouse_name,
                "quantity": row.quantity,
                "reorder_level": row.reorder_level,
            }
            for row in low_stock_rows
        ]

        # Warehouse breakdown
        wh_stmt = (
            select(
                Warehouse.id.label("warehouse_id"),
                Warehouse.name.label("warehouse_name"),
                func.coalesce(func.sum(Inventory.quantity), 0).label("total_qty"),
                func.count(distinct(Inventory.product_id)).label("unique_products"),
                func.coalesce(
                    func.sum(
                        case(
                            (Inventory.quantity <= Inventory.reorder_level, 1),
                            else_=0,
                        )
                    ),
                    0,
                ).label("low_stock"),
            )
            .join(Inventory, Inventory.warehouse_id == Warehouse.id, isouter=True)
            .group_by(Warehouse.id, Warehouse.name)
            .order_by(Warehouse.id.asc())
        )
        wh_rows = db.execute(wh_stmt).all()
        by_warehouse = [
            {
                "warehouse_id": row.warehouse_id,
                "warehouse_name": row.warehouse_name,
                "total_quantity": int(row.total_qty),
                "unique_products_count": int(row.unique_products),
                "low_stock_count": int(row.low_stock),
            }
            for row in wh_rows
        ]

        return {
            "total_inventory_records": int(gross_row.total_records or 0),
            "total_available_quantity": int(gross_row.total_qty or 0),
            "low_stock_products_count": int(gross_row.low_stock_count or 0),
            "low_stock_products": low_stock_products,
            "by_warehouse": by_warehouse,
        }

    @staticmethod
    def get_warehouse_analytics(db: Session) -> Dict[str, Any]:
        """
        Calculates active vs inactive warehouse counts and capacity/stock summaries.
        """
        # Active and inactive counts
        counts_stmt = select(
            func.count(Warehouse.id).label("total"),
            func.coalesce(
                func.sum(case((Warehouse.is_active.is_(True), 1), else_=0)),
                0,
            ).label("active"),
            func.coalesce(
                func.sum(case((Warehouse.is_active.is_(False), 1), else_=0)),
                0,
            ).label("inactive"),
        )
        counts_row = db.execute(counts_stmt).one()

        # Detailed warehouse summaries
        summary_stmt = (
            select(
                Warehouse.id,
                Warehouse.name,
                Warehouse.location,
                Warehouse.capacity,
                Warehouse.is_active,
                func.count(distinct(Inventory.product_id)).label("total_products"),
                func.coalesce(func.sum(Inventory.quantity), 0).label("total_stock"),
                func.coalesce(
                    func.sum(
                        case(
                            (Inventory.quantity <= Inventory.reorder_level, 1),
                            else_=0,
                        )
                    ),
                    0,
                ).label("low_stock"),
            )
            .join(Inventory, Inventory.warehouse_id == Warehouse.id, isouter=True)
            .group_by(
                Warehouse.id,
                Warehouse.name,
                Warehouse.location,
                Warehouse.capacity,
                Warehouse.is_active,
            )
            .order_by(Warehouse.id.asc())
        )
        summary_rows = db.execute(summary_stmt).all()
        warehouses_summary = [
            {
                "warehouse_id": row.id,
                "name": row.name,
                "location": row.location,
                "capacity": row.capacity,
                "is_active": row.is_active,
                "total_products": int(row.total_products),
                "total_stock_quantity": int(row.total_stock),
                "low_stock_items": int(row.low_stock),
            }
            for row in summary_rows
        ]

        return {
            "total_warehouses": int(counts_row.total or 0),
            "active_warehouses": int(counts_row.active or 0),
            "inactive_warehouses": int(counts_row.inactive or 0),
            "warehouses_summary": warehouses_summary,
        }

    @staticmethod
    def get_route_analytics(
        db: Session,
        start_datetime: Optional[datetime] = None,
        end_datetime: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Aggregates route lifecycle states and assigned shipment volume.
        """
        # Status distribution
        status_stmt = select(
            Route.status,
            func.count(Route.id).label("count"),
        ).group_by(Route.status)

        if start_datetime is not None:
            status_stmt = status_stmt.where(Route.created_at >= start_datetime)
        if end_datetime is not None:
            status_stmt = status_stmt.where(Route.created_at <= end_datetime)

        status_rows = db.execute(status_stmt).all()

        by_status: Dict[str, int] = {s.value: 0 for s in RouteStatus}
        total_routes = 0
        for row in status_rows:
            st = row[0].value if hasattr(row[0], "value") else str(row[0])
            count = int(row[1])
            by_status[st] = count
            total_routes += count

        # Active & completed counts
        active_count = (
            db.scalar(
                select(func.count(Route.id)).where(
                    Route.status == RouteStatus.ACTIVE,
                    Route.is_active.is_(True),
                )
            )
            or 0
        )
        completed_count = by_status.get(RouteStatus.COMPLETED.value, 0)

        # Total shipments assigned across all routes
        total_shipments_assigned = (
            db.scalar(select(func.count(RouteShipment.id))) or 0
        )

        # Routes summary
        routes_stmt = (
            select(
                Route.id,
                Route.name,
                Route.origin,
                Route.destination,
                Route.status,
                Route.is_active,
                func.count(RouteShipment.id).label("shipment_count"),
            )
            .join(RouteShipment, RouteShipment.route_id == Route.id, isouter=True)
            .group_by(
                Route.id,
                Route.name,
                Route.origin,
                Route.destination,
                Route.status,
                Route.is_active,
            )
            .order_by(Route.id.asc())
        )
        if start_datetime is not None:
            routes_stmt = routes_stmt.where(Route.created_at >= start_datetime)
        if end_datetime is not None:
            routes_stmt = routes_stmt.where(Route.created_at <= end_datetime)

        routes_rows = db.execute(routes_stmt).all()
        routes_summary = [
            {
                "route_id": row.id,
                "name": row.name,
                "origin": row.origin,
                "destination": row.destination,
                "status": row.status.value if hasattr(row.status, "value") else str(row.status),
                "is_active": row.is_active,
                "shipments_assigned_count": int(row.shipment_count),
            }
            for row in routes_rows
        ]

        return {
            "total_routes": total_routes,
            "active_routes": active_count,
            "completed_routes": completed_count,
            "by_status": by_status,
            "total_shipments_assigned": total_shipments_assigned,
            "routes_summary": routes_summary,
        }


analytics_repository = AnalyticsRepository()
