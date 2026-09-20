"""
Route Service
=============
Business logic layer managing transit route operations, validations,
RBAC coordination, soft deletion, and transactional shipment allocations.
"""

from decimal import Decimal
from typing import List, Optional, Union
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.route import Route, RouteStatus
from app.models.shipment import Shipment
from app.models.user import User
from app.repositories.route_repository import route_repository
from app.repositories.shipment_repository import shipment_repository
from app.schemas.route import RouteCreate, RouteUpdate


class RouteService:
    """
    Business service for Route management and logistics corridor assignment.
    """

    def __init__(
        self,
        repository=route_repository,
        shipment_repo=shipment_repository,
    ):
        self.repository = repository
        self.shipment_repo = shipment_repo

    def create_route(self, db: Session, payload: RouteCreate) -> Route:
        """
        Validates required fields and operational metrics, then persists a new route.
        """
        # Validate required origin and destination
        origin = payload.origin.strip()
        destination = payload.destination.strip()
        name = payload.name.strip()

        if not name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Route name cannot be empty",
            )
        if not origin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Route origin cannot be empty",
            )
        if not destination:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Route destination cannot be empty",
            )

        # Validate non-negative metrics
        if payload.estimated_distance is not None and payload.estimated_distance < Decimal(0):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Estimated distance must be non-negative",
            )
        if payload.estimated_duration is not None and payload.estimated_duration < Decimal(0):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Estimated duration must be non-negative",
            )

        route = Route(
            name=name,
            origin=origin,
            destination=destination,
            estimated_distance=payload.estimated_distance,
            estimated_duration=payload.estimated_duration,
            status=payload.status,
            is_active=True,
        )

        created_route = self.repository.create(db, route)
        created_route.shipments_count = 0
        return created_route

    def get_route(self, db: Session, route_id: int) -> Route:
        """
        Retrieves a single route by ID, raising HTTP 404 if not found.
        """
        route = self.repository.get_by_id(db, route_id)
        if not route:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Route with ID {route_id} was not found",
            )
        route.shipments_count = self.repository.get_shipments_count(db, route_id)
        return route

    def list_routes(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status_filter: Optional[Union[RouteStatus, str]] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
    ) -> List[Route]:
        """
        Retrieves a paginated list of routes with optional status and active filtering.
        """
        parsed_status: Optional[RouteStatus] = None
        if status_filter:
            if isinstance(status_filter, RouteStatus):
                parsed_status = status_filter
            else:
                try:
                    parsed_status = RouteStatus(status_filter.strip().upper())
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid route status filter: '{status_filter}'",
                    )

        routes = self.repository.get_all(
            db,
            skip=skip,
            limit=limit,
            status=parsed_status,
            is_active=is_active,
            search=search,
        )
        for r in routes:
            r.shipments_count = self.repository.get_shipments_count(db, r.id)
        return routes

    def update_route(
        self,
        db: Session,
        route_id: int,
        payload: RouteUpdate,
    ) -> Route:
        """
        Updates an existing route with non-empty fields from payload.
        Raises HTTP 404 if not found.
        """
        route = self.get_route(db, route_id)

        update_data = payload.model_dump(exclude_unset=True)

        # Validate non-negative metrics
        if "estimated_distance" in update_data and update_data["estimated_distance"] is not None:
            if update_data["estimated_distance"] < Decimal(0):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Estimated distance must be non-negative",
                )

        if "estimated_duration" in update_data and update_data["estimated_duration"] is not None:
            if update_data["estimated_duration"] < Decimal(0):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Estimated duration must be non-negative",
                )

        # Clean string inputs
        for field in ("name", "origin", "destination"):
            if field in update_data and update_data[field] is not None:
                cleaned = update_data[field].strip()
                if not cleaned:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Route {field} cannot be empty",
                    )
                update_data[field] = cleaned

        if update_data:
            route = self.repository.update(db, route, update_data)

        route.shipments_count = self.repository.get_shipments_count(db, route.id)
        return route

    def delete_route(self, db: Session, route_id: int) -> Route:
        """
        Soft-deletes a route by setting `is_active = False`.
        Raises HTTP 404 if not found.
        """
        route = self.get_route(db, route_id)
        deleted = self.repository.soft_delete(db, route)
        deleted.shipments_count = self.repository.get_shipments_count(db, route_id)
        return deleted

    def assign_shipments_to_route(
        self,
        db: Session,
        route_id: int,
        shipment_ids: List[int],
        current_user: Optional[User] = None,
    ) -> List[Shipment]:
        """
        Assigns one or more shipments to a route transactionally.
        Validates route and shipment existence, prevents duplicate allocations,
        and ensures transactional integrity.
        """
        # 1. Validate route exists (404 if not found)
        route = self.repository.get_by_id(db, route_id)
        if not route:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Route with ID {route_id} was not found",
            )

        if not shipment_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one shipment ID must be provided",
            )

        # 2. Prevent duplicate IDs within the incoming request
        if len(shipment_ids) != len(set(shipment_ids)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Duplicate shipment IDs provided in assignment request",
            )

        # 3. Validate each shipment exists and is not already assigned
        for s_id in shipment_ids:
            shipment = self.shipment_repo.get_by_id(db, s_id)
            if not shipment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Shipment with ID {s_id} does not exist",
                )

            existing_assignment = self.repository.get_route_shipment(db, route_id, s_id)
            if existing_assignment:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Shipment with ID {s_id} is already assigned to route {route_id}",
                )

        # 4. Perform transactional assignment
        user_id = current_user.id if current_user else None
        try:
            return self.repository.assign_shipments(
                db,
                route_id=route_id,
                shipment_ids=shipment_ids,
                assigned_by_user_id=user_id,
            )
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Database integrity error during shipment allocation",
            )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal error occurred while assigning shipments to route",
            )

    def get_route_shipments(self, db: Session, route_id: int) -> List[Shipment]:
        """
        Retrieves all shipments assigned to a route.
        Raises HTTP 404 if the route does not exist.
        """
        # Validate route exists
        route = self.repository.get_by_id(db, route_id)
        if not route:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Route with ID {route_id} was not found",
            )

        return self.repository.get_route_shipments(db, route_id)


route_service = RouteService()
