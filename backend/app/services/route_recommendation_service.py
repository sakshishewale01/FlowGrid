"""Explainable route recommendations using existing route and fleet records only."""

from decimal import Decimal
from typing import List

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.route import Route, RouteStatus
from app.models.vehicle import Vehicle
from app.schemas.route_recommendation import (
    RouteRecommendation,
    RouteRecommendationRequest,
    RouteRecommendationResponse,
)


class RouteRecommendationService:
    def recommend(
        self, db: Session, payload: RouteRecommendationRequest
    ) -> RouteRecommendationResponse:
        origin = payload.origin.strip().lower()
        destination = payload.destination.strip().lower()
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
            vehicles = [vehicle]
        else:
            query = db.query(Vehicle).filter(Vehicle.status == "AVAILABLE")
            if payload.shipment_weight_kg is not None:
                query = query.filter(Vehicle.capacity >= payload.shipment_weight_kg)
            vehicles = query.order_by(Vehicle.capacity.asc()).all()

        recommendations: List[RouteRecommendation] = []
        for route in routes:
            exact_origin = route.origin.strip().lower() == origin
            exact_destination = route.destination.strip().lower() == destination
            if payload.shipment_weight_kg is not None and payload.vehicle_id is not None:
                if not vehicles or Decimal(str(vehicles[0].capacity)) < payload.shipment_weight_kg:
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
                )
            )
        recommendations.sort(key=lambda item: item.score, reverse=True)
        return RouteRecommendationResponse(
            recommendations=recommendations[: payload.limit],
            methodology="Matches active/planned database routes by origin and destination, then ranks exact matches by estimated duration and distance.",
            limitations=["Estimated route records only; no road-network, traffic, GPS, or telemetry optimization is performed."],
        )


route_recommendation_service = RouteRecommendationService()
