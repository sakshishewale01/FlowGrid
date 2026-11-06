"""Explainable route recommendations using existing route and fleet records only."""

from decimal import Decimal
from typing import List

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.route import Route, RouteStatus, RouteShipment
from app.models.vehicle import Vehicle
from app.repositories.shipment_repository import shipment_repository
from app.services.route_service import route_service
from app.schemas.route_recommendation import (
    RouteRecommendation,
    RouteRecommendationRequest,
    RouteRecommendationResponse,
)


class RouteRecommendationService:
    def recommend(
        self, db: Session, payload: RouteRecommendationRequest
    ) -> RouteRecommendationResponse:
        shipment = shipment_repository.get_by_id(db, payload.shipment_id) if payload.shipment_id else None
        if payload.shipment_id and shipment is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found")
        origin_value = payload.origin or (shipment.origin_warehouse.location if shipment and shipment.origin_warehouse else None)
        destination_value = payload.destination or (shipment.destination_city if shipment else None)
        if not origin_value or not destination_value:
            return RouteRecommendationResponse(
                recommendations=[],
                methodology="Uses stored route records and shipment/warehouse fields when available.",
                limitations=["The shipment has insufficient origin warehouse or destination data for a route comparison."],
            )
        origin = origin_value.strip().lower()
        destination = destination_value.strip().lower()
        requested_weight = payload.shipment_weight_kg
        if requested_weight is None and shipment:
            requested_weight = shipment.total_weight_kg
        if not origin or not destination:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Origin and destination are required")

        routes = (
            db.query(Route)
            .filter(Route.is_active.is_(True), Route.status.in_([RouteStatus.ACTIVE, RouteStatus.PLANNED]))
            .filter(
                or_(
                    Route.origin.ilike(f"%{origin}%"),
                    Route.destination.ilike(f"%{destination}%"),
                    (Route.origin.ilike(f"%{origin}%") & Route.destination.ilike(f"%{destination}%")),
                )
            )
            .all()
        )
        if not routes:
            return RouteRecommendationResponse(
                recommendations=[],
                methodology="Matches active/planned database routes by origin and destination, then ranks exact matches by estimated duration and distance.",
                limitations=["No matching route exists in the current database.", "This is an estimate and does not use road-network, traffic, GPS, or telemetry data."],
            )

        vehicles = []
        if payload.vehicle_id is not None:
            vehicle = db.get(Vehicle, payload.vehicle_id)
            if vehicle is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
            if vehicle.status != "AVAILABLE":
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Vehicle is not available for recommendation")
            vehicles = [vehicle]
        else:
            query = db.query(Vehicle).filter(Vehicle.status == "AVAILABLE")
            if requested_weight is not None:
                query = query.filter(Vehicle.capacity >= requested_weight)
            vehicles = query.order_by(Vehicle.capacity.asc()).all()

        recommendations: List[RouteRecommendation] = []
        for route in routes:
            exact_origin = route.origin.strip().lower() == origin
            exact_destination = route.destination.strip().lower() == destination
            if requested_weight is not None and payload.vehicle_id is not None:
                if not vehicles or Decimal(str(vehicles[0].capacity)) < requested_weight:
                    continue
            score = 100.0 - (0 if exact_origin else 20) - (0 if exact_destination else 20)
            if route.estimated_duration is not None:
                score -= min(float(route.estimated_duration), 40.0) / 4
            if route.estimated_distance is not None:
                score -= min(float(route.estimated_distance), 4000.0) / 400
            selected_vehicle = vehicles[0] if vehicles else None
            explanation = [
                "Active or planned route matched against the requested corridor.",
                "Ranked using exact endpoint matches, then stored estimated duration and distance.",
            ]
            if selected_vehicle:
                explanation.append(f"Vehicle {selected_vehicle.registration_number} is available in the fleet records.")
            else:
                explanation.append("No capacity-compatible available vehicle was found; vehicle assignment remains manual.")
            constraints = []
            if route.estimated_distance is None or route.estimated_duration is None:
                constraints.append("Stored distance or duration is missing; comparison is incomplete.")
            if requested_weight is not None and selected_vehicle is None:
                constraints.append("No available vehicle in the stored fleet has sufficient capacity.")
            recommendations.append(
                RouteRecommendation(
                    route_id=route.id,
                    route_name=route.name,
                    origin=route.origin,
                    destination=route.destination,
                    estimated_distance=route.estimated_distance,
                    estimated_duration=route.estimated_duration,
                    score=round(max(score, 0), 2),
                    explanation=explanation,
                    vehicle_id=selected_vehicle.id if selected_vehicle else None,
                    vehicle_capacity_kg=selected_vehicle.capacity if selected_vehicle else None,
                    shipment_id=payload.shipment_id,
                    capacity_feasible=selected_vehicle is not None or requested_weight is None,
                    constraints=constraints,
                )
            )
        recommendations.sort(key=lambda item: item.score, reverse=True)
        return RouteRecommendationResponse(
            recommendations=recommendations[: payload.limit],
            methodology="Matches active/planned database routes by origin and destination, then ranks exact matches by estimated duration and distance.",
            limitations=["Estimated route records only; no road-network, traffic, GPS, or telemetry optimization is performed."],
        )

    def approve(
        self, db: Session, route_id: int, payload, current_user
    ):
        route = db.get(Route, route_id)
        if route is None or not route.is_active or route.status not in (RouteStatus.ACTIVE, RouteStatus.PLANNED):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only active or planned routes can be approved")
        shipment = shipment_repository.get_by_id(db, payload.shipment_id)
        if shipment is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found")
        if db.query(RouteShipment).filter(RouteShipment.shipment_id == shipment.id).first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Shipment is already assigned to a route")
        vehicle_id = payload.vehicle_id
        if vehicle_id is None:
            vehicle_query = db.query(Vehicle).filter(Vehicle.status == "AVAILABLE")
            if shipment.total_weight_kg is not None:
                vehicle_query = vehicle_query.filter(Vehicle.capacity >= shipment.total_weight_kg)
            vehicle = vehicle_query.order_by(Vehicle.capacity.asc()).first()
            vehicle_id = vehicle.id if vehicle else None
        route_service.assign_shipments_to_route(
            db, route_id, [shipment.id], current_user=current_user, vehicle_id=vehicle_id
        )
        return {"route_id": route_id, "shipment_id": shipment.id, "vehicle_id": vehicle_id, "message": "Recommendation approved and assignment applied"}


route_recommendation_service = RouteRecommendationService()
