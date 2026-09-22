"""
FlowGrid - AI Pipeline Feature Engineering
==========================================
Transforms raw operational contexts into normalized, leak-free feature vectors
and supervised target labels according to ML engineering best practices.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from app.pipeline.schema import DatasetRecord
from app.pipeline.feature_extractor import ExtractedShipmentContext
from app.models.shipment import ShipmentStatus


class FeatureEngineer:
    """
    Transforms extracted shipment context into an ML-ready DatasetRecord.
    """

    @staticmethod
    def transform(ctx: ExtractedShipmentContext) -> DatasetRecord:
        """
        Builds a flattened, deterministic feature vector for the given shipment context.
        Strictly isolates target variables to avoid data leakage.
        """
        s = ctx.shipment
        w = ctx.warehouse
        v = ctx.vehicle
        d = ctx.driver
        r = ctx.route

        # Convert numerics safely
        weight_kg = float(s.total_weight_kg) if s.total_weight_kg is not None else None
        volume_cbm = float(s.total_volume_cbm) if s.total_volume_cbm is not None else None
        veh_capacity_kg = float(v.capacity) if v and v.capacity is not None else None
        wh_capacity = int(w.capacity) if w and w.capacity is not None else None
        route_dist_km = float(r.estimated_distance) if r and r.estimated_distance is not None else None
        route_dur_hrs = float(r.estimated_duration) if r and r.estimated_duration is not None else None

        # Binary allocation indicators
        has_driver = 1 if d is not None else 0
        has_vehicle = 1 if v is not None else 0
        has_route = 1 if r is not None else 0

        # Capacity utilization ratio
        weight_utilization: Optional[float] = None
        if weight_kg is not None and veh_capacity_kg is not None and veh_capacity_kg > 0:
            weight_utilization = round(min(1.0, weight_kg / veh_capacity_kg), 4)

        # Temporal features based on scheduled pickup (or creation time fallback)
        temporal_ref: Optional[datetime] = s.scheduled_pickup_at or s.created_at
        scheduled_iso: Optional[str] = (
            s.scheduled_pickup_at.isoformat() if s.scheduled_pickup_at else None
        )
        pickup_hour: Optional[int] = temporal_ref.hour if temporal_ref else None
        pickup_dow: Optional[int] = temporal_ref.weekday() if temporal_ref else None
        pickup_month: Optional[int] = temporal_ref.month if temporal_ref else None
        is_weekend: Optional[int] = (
            1 if temporal_ref and temporal_ref.weekday() in (5, 6) else 0
        ) if temporal_ref else None

        # Interstate transit heuristic
        is_interstate = 0
        if w and w.location and s.destination_state:
            # Check if destination state code appears in warehouse location string
            dest_st = s.destination_state.strip().upper()
            wh_loc = w.location.strip().upper()
            if dest_st not in wh_loc:
                is_interstate = 1

        # Supervised target calculation (ONLY for completed/delivered shipments)
        actual_pickup_iso: Optional[str] = (
            ctx.actual_pickup_at.isoformat() if ctx.actual_pickup_at else None
        )
        actual_delivery_iso: Optional[str] = (
            ctx.actual_delivered_at.isoformat() if ctx.actual_delivered_at else None
        )

        actual_duration_hours: Optional[float] = None
        is_delayed: Optional[int] = None
        delay_hours: Optional[float] = None

        if s.status == ShipmentStatus.DELIVERED and ctx.actual_pickup_at and ctx.actual_delivered_at:
            delta_seconds = (ctx.actual_delivered_at - ctx.actual_pickup_at).total_seconds()
            if delta_seconds >= 0:
                actual_duration_hours = round(delta_seconds / 3600.0, 4)

                # Delay target derivation
                if route_dur_hrs is not None and route_dur_hrs > 0:
                    # Delay defined as delivery exceeding planned corridor duration
                    delay_delta = actual_duration_hours - route_dur_hrs
                    if delay_delta > 0.1:  # 6-minute buffer
                        is_delayed = 1
                        delay_hours = round(delay_delta, 4)
                    else:
                        is_delayed = 0
                        delay_hours = 0.0
                else:
                    # If route duration is absent, flag delay based on audit history signals
                    is_delayed = 1 if ctx.delay_signals_count > 0 else 0
                    delay_hours = None

        return DatasetRecord(
            shipment_id=s.id,
            tracking_number=s.tracking_number,
            created_timestamp=s.created_at.isoformat() if s.created_at else "",
            origin_warehouse_id=s.origin_warehouse_id,
            destination_city=s.destination_city,
            destination_state=s.destination_state,
            destination_postal_code=s.destination_postal_code,
            cargo_weight_kg=weight_kg,
            cargo_volume_cbm=volume_cbm,
            shipment_status=s.status.value,
            assigned_driver_id=d.id if d else None,
            driver_is_active=d.user.is_active if d and d.user else None,
            driver_availability_status=d.availability_status if d else None,
            assigned_vehicle_id=v.id if v else None,
            vehicle_type=v.vehicle_type if v else None,
            vehicle_capacity_kg=veh_capacity_kg,
            vehicle_status=v.status if v else None,
            warehouse_name=w.name if w else None,
            warehouse_location=w.location if w else None,
            warehouse_capacity=wh_capacity,
            route_id=r.id if r else None,
            route_name=r.name if r else None,
            planned_distance_km=route_dist_km,
            planned_duration_hours=route_dur_hrs,
            has_driver_assigned=has_driver,
            has_vehicle_assigned=has_vehicle,
            has_route_assigned=has_route,
            weight_capacity_utilization=weight_utilization,
            scheduled_pickup_timestamp=scheduled_iso,
            scheduled_pickup_hour=pickup_hour,
            scheduled_pickup_day_of_week=pickup_dow,
            scheduled_pickup_month=pickup_month,
            is_weekend=is_weekend,
            is_interstate=is_interstate,
            historical_delay_signals_count=ctx.delay_signals_count,
            actual_pickup_timestamp=actual_pickup_iso,
            actual_delivery_timestamp=actual_delivery_iso,
            actual_duration_hours=actual_duration_hours,
            is_delayed=is_delayed,
            delay_hours=delay_hours,
        )


feature_engineer = FeatureEngineer()
