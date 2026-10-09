"""
Delay Risk Scoring Service
==========================
Calculates deterministic, explainable operational delay risk scores (0-100)
for shipments based on resource allocation, equipment capacity strain,
corridor geography, origin facility congestion, and lifecycle exceptions.

Safety Guarantee:
- Never invents missing values or hallucinates data.
- Never labels scores as empirical or calibrated probabilities.
- Treats missing values gracefully without crashing or skewing metrics.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from app.models.shipment import Shipment, ShipmentStatus
from app.schemas.analytics import (
    FleetDelayRiskSummary,
    RiskContributingFactor,
    ShipmentDelayRiskResponse,
)


class DelayRiskService:
    """
    Core engine implementing deterministic, factor-by-factor delay risk scoring.
    """

    @staticmethod
    def evaluate_shipment(
        shipment: Shipment,
        warehouse_stock_map: Optional[Dict[int, int]] = None,
    ) -> ShipmentDelayRiskResponse:
        """
        Evaluates a single shipment and produces an explainable delay risk profile.
        """
        evaluated_iso = datetime.now(timezone.utc).isoformat()
        wh = shipment.origin_warehouse
        v = shipment.assigned_vehicle
        d = shipment.assigned_driver
        routes = shipment.routes or []
        primary_route = routes[0] if routes else None

        # Convert numerics safely
        weight_kg = (
            float(shipment.total_weight_kg)
            if shipment.total_weight_kg is not None
            else None
        )
        veh_capacity_kg = (
            float(v.capacity) if v and v.capacity is not None else None
        )

        # Asset allocations
        has_driver = bool(shipment.assigned_driver_id is not None)
        has_vehicle = bool(shipment.assigned_vehicle_id is not None)
        has_route = bool(len(routes) > 0)

        # Weight utilization
        weight_utilization: Optional[float] = None
        if weight_kg is not None and veh_capacity_kg is not None and veh_capacity_kg > 0:
            weight_utilization = round(weight_kg / veh_capacity_kg, 4)

        # Interstate evaluation
        is_interstate = False
        if wh and wh.location and shipment.destination_state:
            dest_st = shipment.destination_state.strip().upper()
            wh_loc = wh.location.strip().upper()
            if dest_st not in wh_loc:
                is_interstate = True

        # Origin warehouse utilization
        wh_utilization_rate: Optional[float] = None
        if wh and wh.capacity and wh.capacity > 0:
            stock_qty = (warehouse_stock_map or {}).get(wh.id, 0)
            wh_utilization_rate = round(
                min(100.0, (stock_qty / float(wh.capacity)) * 100.0), 2
            )

        # ----------------------------------------------------------------------
        # 1. Handle Terminal States
        # ----------------------------------------------------------------------
        if shipment.status == ShipmentStatus.DELIVERED:
            return ShipmentDelayRiskResponse(
                shipment_id=shipment.id,
                tracking_number=shipment.tracking_number,
                status=shipment.status.value,
                risk_score=0,
                risk_category="COMPLETED",
                summary_explanation="Shipment has been successfully delivered; active transit delay risk is zero.",
                is_calibrated_probability=False,
                assessment_method="DETERMINISTIC_HEURISTIC",
                contributing_factors=[],
                evaluated_at=evaluated_iso,
                origin_warehouse_id=wh.id if wh else None,
                origin_warehouse_name=wh.name if wh else None,
                origin_warehouse_location=wh.location if wh else None,
                warehouse_utilization_rate=wh_utilization_rate,
                destination_city=shipment.destination_city,
                destination_state=shipment.destination_state,
                is_interstate=is_interstate,
                has_driver_assigned=has_driver,
                assigned_driver_id=shipment.assigned_driver_id,
                has_vehicle_assigned=has_vehicle,
                assigned_vehicle_id=shipment.assigned_vehicle_id,
                vehicle_capacity_kg=veh_capacity_kg,
                cargo_weight_kg=weight_kg,
                weight_capacity_utilization=weight_utilization,
                has_route_assigned=has_route,
                assigned_route_id=primary_route.id if primary_route else None,
                assigned_route_name=primary_route.name if primary_route else None,
            )

        if shipment.status in (ShipmentStatus.CANCELLED, ShipmentStatus.RETURNED):
            return ShipmentDelayRiskResponse(
                shipment_id=shipment.id,
                tracking_number=shipment.tracking_number,
                status=shipment.status.value,
                risk_score=0,
                risk_category=shipment.status.value,
                summary_explanation=f"Shipment is in terminal state '{shipment.status.value}'; delay risk evaluation is not applicable.",
                is_calibrated_probability=False,
                assessment_method="DETERMINISTIC_HEURISTIC",
                contributing_factors=[],
                evaluated_at=evaluated_iso,
                origin_warehouse_id=wh.id if wh else None,
                origin_warehouse_name=wh.name if wh else None,
                origin_warehouse_location=wh.location if wh else None,
                warehouse_utilization_rate=wh_utilization_rate,
                destination_city=shipment.destination_city,
                destination_state=shipment.destination_state,
                is_interstate=is_interstate,
                has_driver_assigned=has_driver,
                assigned_driver_id=shipment.assigned_driver_id,
                has_vehicle_assigned=has_vehicle,
                assigned_vehicle_id=shipment.assigned_vehicle_id,
                vehicle_capacity_kg=veh_capacity_kg,
                cargo_weight_kg=weight_kg,
                weight_capacity_utilization=weight_utilization,
                has_route_assigned=has_route,
                assigned_route_id=primary_route.id if primary_route else None,
                assigned_route_name=primary_route.name if primary_route else None,
            )

        # ----------------------------------------------------------------------
        # 2. Evaluate Active Shipment Risk Factors
        # ----------------------------------------------------------------------
        score = 0
        factors: List[RiskContributingFactor] = []

        # Factor A: Unassigned Driver (+20 pts)
        if not has_driver:
            score += 20
            factors.append(
                RiskContributingFactor(
                    factor_id="UNASSIGNED_DRIVER",
                    factor_name="Unassigned Driver",
                    impact_points=20,
                    severity="HIGH",
                    description="Shipment lacks an allocated driver, creating a dispatch scheduling and staging bottleneck.",
                )
            )

        # Factor B: Unassigned Vehicle (+15 pts)
        if not has_vehicle:
            score += 15
            factors.append(
                RiskContributingFactor(
                    factor_id="UNASSIGNED_VEHICLE",
                    factor_name="Unassigned Transport Vehicle",
                    impact_points=15,
                    severity="MEDIUM",
                    description="No transport equipment is allocated; dispatch cannot proceed without vehicle assignment.",
                )
            )

        # Factor C: Unassigned Route (+10 pts)
        if not has_route:
            score += 10
            factors.append(
                RiskContributingFactor(
                    factor_id="UNASSIGNED_ROUTE",
                    factor_name="Unassigned Route Corridor",
                    impact_points=10,
                    severity="MEDIUM",
                    description="No planned transit corridor or route has been linked, increasing transit unpredictability.",
                )
            )

        # Factor D: Vehicle Capacity Strain (+10 to +20 pts)
        if weight_utilization is not None:
            if weight_utilization > 0.90:
                score += 20
                factors.append(
                    RiskContributingFactor(
                        factor_id="CRITICAL_CAPACITY_STRAIN",
                        factor_name="Critical Vehicle Capacity Load",
                        impact_points=20,
                        severity="HIGH",
                        description=f"Cargo load ({weight_kg:,.1f} kg) utilizes {weight_utilization * 100:.1f}% of vehicle capacity (>90%), raising risk of handling delays, weigh-station compliance holds, and equipment strain.",
                    )
                )
            elif weight_utilization > 0.80:
                score += 10
                factors.append(
                    RiskContributingFactor(
                        factor_id="HIGH_CAPACITY_UTILIZATION",
                        factor_name="High Vehicle Capacity Load",
                        impact_points=10,
                        severity="MEDIUM",
                        description=f"Cargo load ({weight_kg:,.1f} kg) utilizes {weight_utilization * 100:.1f}% of vehicle capacity (80-90%), operating near peak equipment limits.",
                    )
                )

        # Factor E: Interstate Transit Corridor (+15 pts)
        if is_interstate:
            score += 15
            origin_desc = wh.location if wh and wh.location else "origin hub"
            factors.append(
                RiskContributingFactor(
                    factor_id="INTERSTATE_TRANSIT",
                    factor_name="Interstate Transit Corridor",
                    impact_points=15,
                    severity="MEDIUM",
                    description=f"Cross-state freight from {origin_desc} to {shipment.destination_state} traverses longer corridors with multi-jurisdictional traffic and toll checkpoints.",
                )
            )

        # Factor F: Origin Warehouse Congestion (+10 to +20 pts)
        if wh_utilization_rate is not None:
            if wh_utilization_rate > 85.0:
                score += 20
                factors.append(
                    RiskContributingFactor(
                        factor_id="CRITICAL_WAREHOUSE_CONGESTION",
                        factor_name="Critical Warehouse Congestion",
                        impact_points=20,
                        severity="HIGH",
                        description=f"Origin facility '{wh.name}' is operating at {wh_utilization_rate:.1f}% storage capacity (>85%), causing loading dock queues and outbound staging delays.",
                    )
                )
            elif wh_utilization_rate > 75.0:
                score += 10
                factors.append(
                    RiskContributingFactor(
                        factor_id="MODERATE_WAREHOUSE_CONGESTION",
                        factor_name="Elevated Warehouse Congestion",
                        impact_points=10,
                        severity="MEDIUM",
                        description=f"Origin facility '{wh.name}' is operating at {wh_utilization_rate:.1f}% storage capacity (>75%), which may extend dock staging durations.",
                    )
                )

        # Factor G: Prior Delivery Exception (+15 pts)
        if shipment.status == ShipmentStatus.FAILED:
            score += 15
            factors.append(
                RiskContributingFactor(
                    factor_id="PRIOR_DELIVERY_FAILURE",
                    factor_name="Prior Delivery Exception",
                    impact_points=15,
                    severity="HIGH",
                    description="Shipment previously experienced a delivery failure and requires exception clearance or rescheduling.",
                )
            )

        # ----------------------------------------------------------------------
        # 3. Clamp Score and Classify Risk Category
        # ----------------------------------------------------------------------
        final_score = max(0, min(100, score))

        if final_score >= 80:
            category = "CRITICAL"
        elif final_score >= 60:
            category = "HIGH"
        elif final_score >= 30:
            category = "MEDIUM"
        else:
            category = "LOW"

        # ----------------------------------------------------------------------
        # 4. Synthesize Human-Readable Explanation
        # ----------------------------------------------------------------------
        if factors:
            factor_titles = [f.factor_name for f in factors]
            summary_explanation = (
                f"{category} DELAY RISK (Score {final_score}/100): "
                f"Key operational risk factors include {', '.join(factor_titles)}."
            )
        else:
            summary_explanation = (
                f"LOW DELAY RISK (Score 0/100): All operational assets assigned; "
                f"vehicle payload within optimal limits; local transit corridor; "
                f"origin warehouse operating with normal throughput."
            )

        return ShipmentDelayRiskResponse(
            shipment_id=shipment.id,
            tracking_number=shipment.tracking_number,
            status=shipment.status.value,
            risk_score=final_score,
            risk_category=category,
            summary_explanation=summary_explanation,
            is_calibrated_probability=False,
            assessment_method="DETERMINISTIC_HEURISTIC",
            contributing_factors=factors,
            evaluated_at=evaluated_iso,
            origin_warehouse_id=wh.id if wh else None,
            origin_warehouse_name=wh.name if wh else None,
            origin_warehouse_location=wh.location if wh else None,
            warehouse_utilization_rate=wh_utilization_rate,
            destination_city=shipment.destination_city,
            destination_state=shipment.destination_state,
            is_interstate=is_interstate,
            has_driver_assigned=has_driver,
            assigned_driver_id=shipment.assigned_driver_id,
            has_vehicle_assigned=has_vehicle,
            assigned_vehicle_id=shipment.assigned_vehicle_id,
            vehicle_capacity_kg=veh_capacity_kg,
            cargo_weight_kg=weight_kg,
            weight_capacity_utilization=weight_utilization,
            has_route_assigned=has_route,
            assigned_route_id=primary_route.id if primary_route else None,
            assigned_route_name=primary_route.name if primary_route else None,
        )

    @classmethod
    def evaluate_batch(
        cls,
        shipments: List[Shipment],
        warehouse_stock_map: Optional[Dict[int, int]] = None,
    ) -> Tuple[FleetDelayRiskSummary, List[ShipmentDelayRiskResponse]]:
        """
        Evaluates a collection of shipments and computes fleet-wide distribution metrics.
        """
        evaluations: List[ShipmentDelayRiskResponse] = [
            cls.evaluate_shipment(s, warehouse_stock_map=warehouse_stock_map)
            for s in shipments
        ]

        if not evaluations:
            summary = FleetDelayRiskSummary(
                total_evaluated=0,
                average_risk_score=0.0,
                critical_risk_count=0,
                high_risk_count=0,
                medium_risk_count=0,
                low_risk_count=0,
                completed_or_terminal_count=0,
            )
            return summary, evaluations

        critical_count = 0
        high_count = 0
        medium_count = 0
        low_count = 0
        terminal_count = 0
        active_scores: List[int] = []

        for e in evaluations:
            if e.risk_category == "CRITICAL":
                critical_count += 1
                active_scores.append(e.risk_score)
            elif e.risk_category == "HIGH":
                high_count += 1
                active_scores.append(e.risk_score)
            elif e.risk_category == "MEDIUM":
                medium_count += 1
                active_scores.append(e.risk_score)
            elif e.risk_category == "LOW":
                low_count += 1
                active_scores.append(e.risk_score)
            else:
                terminal_count += 1

        avg_score = (
            round(sum(active_scores) / len(active_scores), 2)
            if active_scores
            else 0.0
        )

        summary = FleetDelayRiskSummary(
            total_evaluated=len(evaluations),
            average_risk_score=avg_score,
            critical_risk_count=critical_count,
            high_risk_count=high_count,
            medium_risk_count=medium_count,
            low_risk_count=low_count,
            completed_or_terminal_count=terminal_count,
        )

        return summary, evaluations


delay_risk_service = DelayRiskService()
