"""
Analytics Repository
====================
Encapsulates high-performance SQL aggregation queries and group-by calculations
across Shipments, Inventory, Warehouses, Products, Drivers, Vehicles, and Routes.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy import select, func, cast, Date, case, distinct
from sqlalchemy.orm import Session, joinedload

from app.models.shipment import Shipment, ShipmentStatus
from app.models.warehouse import Warehouse
from app.models.product import Product
from app.models.inventory import Inventory
from app.models.driver import Driver
from app.models.vehicle import Vehicle
from app.models.user import User
from app.models.route import Route, RouteStatus, RouteShipment
from app.models.tracking import ShipmentStatusHistory


class AnalyticsRepository:
    """
    Data access layer for analytical aggregations and KPI calculations.
    Optimized to execute database-level aggregations and avoid full dataset loads.
    """

    @staticmethod
    def _calculate_delivery_performance(
        db: Session,
        start_datetime: Optional[datetime] = None,
        end_datetime: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Computes delivery duration, on-time rate, and delay duration
        for delivered shipments based on actual status history milestones.
        """
        query = (
            db.query(Shipment)
            .options(
                joinedload(Shipment.routes),
                joinedload(Shipment.status_history),
            )
            .filter(Shipment.status == ShipmentStatus.DELIVERED)
        )
        if start_datetime is not None:
            query = query.filter(Shipment.created_at >= start_datetime)
        if end_datetime is not None:
            query = query.filter(Shipment.created_at <= end_datetime)

        delivered_shipments = query.all()
        total_delivered = len(delivered_shipments)

        on_time_count = 0
        late_count = 0
        durations: List[float] = []
        delay_durations: List[float] = []

        for shipment in delivered_shipments:
            history = sorted(
                shipment.status_history or [],
                key=lambda h: h.created_at or datetime.min,
            )

            actual_pickup_at: Optional[datetime] = None
            for h in history:
                if h.new_status in (ShipmentStatus.PICKED_UP, ShipmentStatus.IN_TRANSIT):
                    actual_pickup_at = h.created_at
                    break
            if actual_pickup_at is None and shipment.scheduled_pickup_at is not None:
                actual_pickup_at = shipment.scheduled_pickup_at

            actual_delivered_at: Optional[datetime] = shipment.delivered_at
            if actual_delivered_at is None:
                for h in history:
                    if h.new_status == ShipmentStatus.DELIVERED:
                        actual_delivered_at = h.created_at
                        break

            delay_signals = 0
            for h in history:
                if h.new_status == ShipmentStatus.FAILED:
                    delay_signals += 1
                elif h.remarks and any(k in h.remarks.lower() for k in ("delay", "late", "breakdown", "traffic", "reroute")):
                    delay_signals += 1

            route = shipment.routes[0] if shipment.routes else None
            route_dur_hrs = float(route.estimated_duration) if route and route.estimated_duration is not None else None

            actual_dur_hrs: Optional[float] = None
            if actual_pickup_at and actual_delivered_at:
                delta_sec = (actual_delivered_at - actual_pickup_at).total_seconds()
                if delta_sec >= 0:
                    actual_dur_hrs = round(delta_sec / 3600.0, 4)
                    durations.append(actual_dur_hrs)

            if route_dur_hrs is not None and route_dur_hrs > 0 and actual_dur_hrs is not None:
                delay_delta = actual_dur_hrs - route_dur_hrs
                if delay_delta > 0.1:  # 6-minute buffer
                    late_count += 1
                    delay_durations.append(round(delay_delta, 4))
                else:
                    on_time_count += 1
            elif delay_signals > 0:
                late_count += 1
            else:
                on_time_count += 1

        on_time_rate = (
            round((on_time_count / total_delivered) * 100.0, 2)
            if total_delivered > 0
            else 0.0
        )
        late_rate = (
            round((late_count / total_delivered) * 100.0, 2)
            if total_delivered > 0
            else 0.0
        )
        avg_duration = (
            round(sum(durations) / len(durations), 2)
            if durations
            else None
        )
        avg_delay = (
            round(sum(delay_durations) / len(delay_durations), 2)
            if delay_durations
            else None
        )

        return {
            "on_time_delivery_rate": on_time_rate,
            "late_delivery_rate": late_rate,
            "average_delivery_duration_hours": avg_duration,
            "average_delay_duration_hours": avg_delay,
        }

    @staticmethod
    def get_overview_statistics(
        db: Session,
        start_datetime: Optional[datetime] = None,
        end_datetime: Optional[datetime] = None,
    ) -> Dict[str, Any]:
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

        # 6. Fleet Vehicles
        total_vehicles = db.scalar(select(func.count(Vehicle.id))) or 0
        available_vehicles = (
            db.scalar(
                select(func.count(Vehicle.id)).where(Vehicle.status == "AVAILABLE")
            )
            or 0
        )

        # 7. Delivery Performance
        delivery_perf = AnalyticsRepository._calculate_delivery_performance(
            db, start_datetime, end_datetime
        )

        # 8. Warehouse Capacity Utilization
        active_wh_capacity = (
            db.scalar(
                select(func.coalesce(func.sum(Warehouse.capacity), 0)).where(
                    Warehouse.is_active.is_(True)
                )
            )
            or 0
        )
        total_inv_qty = (
            db.scalar(select(func.coalesce(func.sum(Inventory.quantity), 0))) or 0
        )
        overall_wh_utilization = (
            round(min(100.0, (total_inv_qty / active_wh_capacity) * 100.0), 2)
            if active_wh_capacity > 0
            else 0.0
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
            "total_vehicles": total_vehicles,
            "available_vehicles": available_vehicles,
            "on_time_delivery_rate": delivery_perf["on_time_delivery_rate"],
            "average_delivery_duration_hours": delivery_perf["average_delivery_duration_hours"],
            "average_delay_duration_hours": delivery_perf["average_delay_duration_hours"],
            "overall_warehouse_utilization_rate": overall_wh_utilization,
        }

    @staticmethod
    def get_shipment_analytics(
        db: Session,
        start_datetime: Optional[datetime] = None,
        end_datetime: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Aggregates shipment distribution by lifecycle status, daily creation date,
        on-time delivery rates, and delay frequencies.
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

        by_status: Dict[str, int] = {s.value: 0 for s in ShipmentStatus}
        total_shipments = 0
        for row in status_rows:
            st = row[0].value if hasattr(row[0], "value") else str(row[0])
            count = int(row[1])
            by_status[st] = count
            total_shipments += count

        # Active shipments count
        active_statuses = [
            ShipmentStatus.CREATED.value,
            ShipmentStatus.CONFIRMED.value,
            ShipmentStatus.ASSIGNED.value,
            ShipmentStatus.PICKED_UP.value,
            ShipmentStatus.IN_TRANSIT.value,
            ShipmentStatus.OUT_FOR_DELIVERY.value,
        ]
        active_count = sum(by_status.get(st, 0) for st in active_statuses)

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

        # Detailed delivery performance
        perf = AnalyticsRepository._calculate_delivery_performance(
            db, start_datetime, end_datetime
        )

        # Historical delay signals count across all shipments in window
        delay_shipment_ids_stmt = select(distinct(ShipmentStatusHistory.shipment_id)).where(
            (ShipmentStatusHistory.new_status == ShipmentStatus.FAILED)
            | (func.lower(ShipmentStatusHistory.remarks).like("%delay%"))
            | (func.lower(ShipmentStatusHistory.remarks).like("%late%"))
            | (func.lower(ShipmentStatusHistory.remarks).like("%breakdown%"))
            | (func.lower(ShipmentStatusHistory.remarks).like("%traffic%"))
            | (func.lower(ShipmentStatusHistory.remarks).like("%reroute%"))
        )
        delay_count_stmt = select(func.count(distinct(Shipment.id))).where(
            (Shipment.status.in_([ShipmentStatus.FAILED, ShipmentStatus.RETURNED]))
            | (Shipment.id.in_(delay_shipment_ids_stmt))
        )
        if start_datetime is not None:
            delay_count_stmt = delay_count_stmt.where(Shipment.created_at >= start_datetime)
        if end_datetime is not None:
            delay_count_stmt = delay_count_stmt.where(Shipment.created_at <= end_datetime)

        delay_shipments_total = db.scalar(delay_count_stmt) or 0
        historical_delay_freq = (
            round((delay_shipments_total / total_shipments) * 100.0, 2)
            if total_shipments > 0
            else 0.0
        )

        return {
            "total_shipments": total_shipments,
            "active_shipments": active_count,
            "by_status": by_status,
            "by_date": by_date,
            "delivery_completion_rate": completion_rate,
            "on_time_delivery_rate": perf["on_time_delivery_rate"],
            "late_delivery_rate": perf["late_delivery_rate"],
            "average_delivery_duration_hours": perf["average_delivery_duration_hours"],
            "average_delay_duration_hours": perf["average_delay_duration_hours"],
            "historical_delay_frequency_rate": historical_delay_freq,
            "cancelled_shipments": cancelled_count,
            "returned_shipments": returned_count,
        }

    @staticmethod
    def get_inventory_analytics(db: Session) -> Dict[str, Any]:
        """
        Calculates global stock balances, safety thresholds, and warehouse breakdowns.
        """
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
        Calculates active vs inactive warehouse counts, capacity utilization,
        and facility summaries.
        """
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
            func.coalesce(
                func.sum(
                    case((Warehouse.is_active.is_(True), Warehouse.capacity), else_=0)
                ),
                0,
            ).label("total_capacity"),
        )
        counts_row = db.execute(counts_stmt).one()

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

        total_inventory_qty = 0
        total_low_stock_items = 0
        warehouses_summary = []

        for row in summary_rows:
            stock = int(row.total_stock)
            cap = int(row.capacity)
            low = int(row.low_stock)
            total_inventory_qty += stock
            total_low_stock_items += low

            utilization = (
                round(min(100.0, (stock / cap) * 100.0), 2) if cap > 0 else 0.0
            )

            warehouses_summary.append(
                {
                    "warehouse_id": row.id,
                    "name": row.name,
                    "location": row.location,
                    "capacity": cap,
                    "is_active": row.is_active,
                    "total_products": int(row.total_products),
                    "total_stock_quantity": stock,
                    "capacity_utilization_rate": utilization,
                    "low_stock_items": low,
                }
            )

        total_active_capacity = int(counts_row.total_capacity or 0)
        overall_utilization = (
            round(
                min(100.0, (total_inventory_qty / total_active_capacity) * 100.0), 2
            )
            if total_active_capacity > 0
            else 0.0
        )

        return {
            "total_warehouses": int(counts_row.total or 0),
            "active_warehouses": int(counts_row.active or 0),
            "inactive_warehouses": int(counts_row.inactive or 0),
            "total_capacity": total_active_capacity,
            "total_inventory_quantity": total_inventory_qty,
            "overall_capacity_utilization_rate": overall_utilization,
            "low_stock_items_count": total_low_stock_items,
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

        total_shipments_assigned = (
            db.scalar(select(func.count(RouteShipment.id))) or 0
        )

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

    @staticmethod
    def get_driver_analytics(db: Session) -> Dict[str, Any]:
        """
        Fleet driver workforce utilization, availability distribution,
        and assigned shipment workload.
        """
        status_stmt = select(
            Driver.availability_status,
            func.count(Driver.id).label("count"),
        ).group_by(Driver.availability_status)
        status_rows = db.execute(status_stmt).all()

        known_statuses = ["AVAILABLE", "ON_DUTY", "IN_TRANSIT", "OFF_DUTY", "SUSPENDED"]
        by_status: Dict[str, int] = {st: 0 for st in known_statuses}
        total_drivers = 0
        for row in status_rows:
            st = str(row[0])
            count = int(row[1])
            by_status[st] = count
            total_drivers += count

        active_drivers_stmt = (
            select(func.count(Driver.id))
            .join(User, User.id == Driver.user_id)
            .where(User.is_active.is_(True))
        )
        active_drivers = db.scalar(active_drivers_stmt) or 0

        available_drivers = by_status.get("AVAILABLE", 0)
        on_duty_drivers = by_status.get("ON_DUTY", 0)
        in_transit_drivers = by_status.get("IN_TRANSIT", 0)
        off_duty_drivers = by_status.get("OFF_DUTY", 0)
        suspended_drivers = by_status.get("SUSPENDED", 0)

        driver_utilization_rate = (
            round(((on_duty_drivers + in_transit_drivers) / active_drivers) * 100.0, 2)
            if active_drivers > 0
            else 0.0
        )

        active_shipment_cond = (
            Shipment.is_active.is_(True)
            & Shipment.status.in_([
                ShipmentStatus.CREATED,
                ShipmentStatus.CONFIRMED,
                ShipmentStatus.ASSIGNED,
                ShipmentStatus.PICKED_UP,
                ShipmentStatus.IN_TRANSIT,
                ShipmentStatus.OUT_FOR_DELIVERY,
            ])
        )

        summary_stmt = (
            select(
                Driver.id,
                Driver.license_number,
                Driver.availability_status,
                User.name.label("user_name"),
                User.is_active.label("user_is_active"),
                func.coalesce(
                    func.sum(
                        case(
                            (active_shipment_cond, 1),
                            else_=0,
                        )
                    ),
                    0,
                ).label("active_shipments_count"),
            )
            .join(User, User.id == Driver.user_id, isouter=True)
            .join(Shipment, Shipment.assigned_driver_id == Driver.id, isouter=True)
            .group_by(
                Driver.id,
                Driver.license_number,
                Driver.availability_status,
                User.name,
                User.is_active,
            )
            .order_by(Driver.id.asc())
        )
        summary_rows = db.execute(summary_stmt).all()
        drivers_summary = [
            {
                "driver_id": row.id,
                "name": row.user_name if row.user_name else f"Driver {row.id}",
                "license_number": row.license_number,
                "availability_status": row.availability_status,
                "is_active": bool(row.user_is_active) if row.user_is_active is not None else False,
                "active_shipments_count": int(row.active_shipments_count),
            }
            for row in summary_rows
        ]

        return {
            "total_drivers": total_drivers,
            "active_drivers": active_drivers,
            "available_drivers": available_drivers,
            "on_duty_drivers": on_duty_drivers,
            "in_transit_drivers": in_transit_drivers,
            "off_duty_drivers": off_duty_drivers,
            "suspended_drivers": suspended_drivers,
            "driver_utilization_rate": driver_utilization_rate,
            "by_status": by_status,
            "drivers_summary": drivers_summary,
        }

    @staticmethod
    def get_vehicle_analytics(db: Session) -> Dict[str, Any]:
        """
        Fleet vehicle utilization, capacity, type distribution,
        and active freight assignments.
        """
        status_stmt = select(
            Vehicle.status,
            func.count(Vehicle.id).label("count"),
        ).group_by(Vehicle.status)
        status_rows = db.execute(status_stmt).all()

        known_statuses = ["AVAILABLE", "IN_USE", "MAINTENANCE", "DECOMMISSIONED"]
        by_status: Dict[str, int] = {st: 0 for st in known_statuses}
        total_vehicles = 0
        for row in status_rows:
            st = str(row[0])
            count = int(row[1])
            by_status[st] = count
            total_vehicles += count

        available_vehicles = by_status.get("AVAILABLE", 0)
        in_use_vehicles = by_status.get("IN_USE", 0)
        maintenance_vehicles = by_status.get("MAINTENANCE", 0)
        decommissioned_vehicles = by_status.get("DECOMMISSIONED", 0)

        type_stmt = select(
            Vehicle.vehicle_type,
            func.count(Vehicle.id).label("count"),
        ).group_by(Vehicle.vehicle_type)
        type_rows = db.execute(type_stmt).all()
        by_type: Dict[str, int] = {str(row[0]): int(row[1]) for row in type_rows}

        total_capacity_kg = float(
            db.scalar(select(func.coalesce(func.sum(Vehicle.capacity), 0))) or 0.0
        )

        vehicle_utilization_rate = (
            round((in_use_vehicles / total_vehicles) * 100.0, 2)
            if total_vehicles > 0
            else 0.0
        )

        active_shipment_cond = (
            Shipment.is_active.is_(True)
            & Shipment.status.in_([
                ShipmentStatus.CREATED,
                ShipmentStatus.CONFIRMED,
                ShipmentStatus.ASSIGNED,
                ShipmentStatus.PICKED_UP,
                ShipmentStatus.IN_TRANSIT,
                ShipmentStatus.OUT_FOR_DELIVERY,
            ])
        )

        summary_stmt = (
            select(
                Vehicle.id,
                Vehicle.registration_number,
                Vehicle.vehicle_type,
                Vehicle.capacity,
                Vehicle.status,
                func.coalesce(
                    func.sum(
                        case(
                            (active_shipment_cond, 1),
                            else_=0,
                        )
                    ),
                    0,
                ).label("active_shipments_count"),
            )
            .join(Shipment, Shipment.assigned_vehicle_id == Vehicle.id, isouter=True)
            .group_by(
                Vehicle.id,
                Vehicle.registration_number,
                Vehicle.vehicle_type,
                Vehicle.capacity,
                Vehicle.status,
            )
            .order_by(Vehicle.id.asc())
        )
        summary_rows = db.execute(summary_stmt).all()
        vehicles_summary = [
            {
                "vehicle_id": row.id,
                "registration_number": row.registration_number,
                "vehicle_type": row.vehicle_type,
                "capacity_kg": float(row.capacity),
                "status": row.status,
                "active_shipments_count": int(row.active_shipments_count),
            }
            for row in summary_rows
        ]

        return {
            "total_vehicles": total_vehicles,
            "available_vehicles": available_vehicles,
            "in_use_vehicles": in_use_vehicles,
            "maintenance_vehicles": maintenance_vehicles,
            "decommissioned_vehicles": decommissioned_vehicles,
            "total_fleet_capacity_kg": total_capacity_kg,
            "vehicle_utilization_rate": vehicle_utilization_rate,
            "by_status": by_status,
            "by_type": by_type,
            "vehicles_summary": vehicles_summary,
        }


analytics_repository = AnalyticsRepository()
