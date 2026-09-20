"""
Route Repository
================
Encapsulates all database query and persistence operations for the Route and RouteShipment models.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy import select, func
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError

from app.models.route import Route, RouteStatus, RouteShipment
from app.models.shipment import Shipment


class RouteRepository:
    """
    Data access layer for route management and shipment allocations.
    """

    @staticmethod
    def get_by_id(db: Session, route_id: int) -> Optional[Route]:
        """
        Retrieves a route by its primary key ID.
        """
        stmt = (
            select(Route)
            .options(joinedload(Route.route_shipments))
            .where(Route.id == route_id)
        )
        return db.scalars(stmt).unique().first()

    @staticmethod
    def get_all(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status: Optional[RouteStatus] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
    ) -> List[Route]:
        """
        Retrieves a paginated list of routes with optional status and active filters.
        """
        stmt = select(Route)

        if status is not None:
            stmt = stmt.where(Route.status == status)

        if is_active is not None:
            stmt = stmt.where(Route.is_active == is_active)

        if search:
            pattern = f"%{search.strip()}%"
            stmt = stmt.where(
                Route.name.ilike(pattern)
                | Route.origin.ilike(pattern)
                | Route.destination.ilike(pattern)
            )

        stmt = stmt.offset(skip).limit(limit).order_by(Route.id.asc())
        return list(db.scalars(stmt).all())

    @staticmethod
    def create(db: Session, route: Route) -> Route:
        """
        Persists a new Route entity into the database.
        """
        db.add(route)
        db.commit()
        db.refresh(route)
        return route

    @staticmethod
    def update(
        db: Session,
        route: Route,
        update_data: Dict[str, Any],
    ) -> Route:
        """
        Updates fields on an existing Route entity.
        """
        for field, value in update_data.items():
            setattr(route, field, value)
        db.commit()
        db.refresh(route)
        return route

    @staticmethod
    def soft_delete(db: Session, route: Route) -> Route:
        """
        Soft-deletes a route by setting `is_active = False`.
        """
        route.is_active = False
        db.commit()
        db.refresh(route)
        return route

    @staticmethod
    def get_route_shipment(
        db: Session,
        route_id: int,
        shipment_id: int,
    ) -> Optional[RouteShipment]:
        """
        Checks whether a specific shipment is currently assigned to a route.
        """
        stmt = select(RouteShipment).where(
            RouteShipment.route_id == route_id,
            RouteShipment.shipment_id == shipment_id,
        )
        return db.scalars(stmt).first()

    @staticmethod
    def assign_shipments(
        db: Session,
        route_id: int,
        shipment_ids: List[int],
        assigned_by_user_id: Optional[int] = None,
    ) -> List[Shipment]:
        """
        Assigns multiple shipments to a route transactionally.
        Rolls back immediately if any error occurs.
        """
        try:
            for s_id in shipment_ids:
                assignment = RouteShipment(
                    route_id=route_id,
                    shipment_id=s_id,
                    assigned_by_user_id=assigned_by_user_id,
                )
                db.add(assignment)
            db.commit()
        except IntegrityError:
            db.rollback()
            raise
        except Exception:
            db.rollback()
            raise

        # Return full shipment entities with relationships eagerly loaded
        return RouteRepository.get_route_shipments(db, route_id)

    @staticmethod
    def get_route_shipments(db: Session, route_id: int) -> List[Shipment]:
        """
        Retrieves all shipments assigned to a specific route,
        eagerly loading warehouse, driver, and vehicle relationships.
        """
        stmt = (
            select(Shipment)
            .join(RouteShipment, RouteShipment.shipment_id == Shipment.id)
            .where(RouteShipment.route_id == route_id)
            .options(
                joinedload(Shipment.origin_warehouse),
                joinedload(Shipment.assigned_driver),
                joinedload(Shipment.assigned_vehicle),
            )
            .order_by(Shipment.id.asc())
        )
        return list(db.scalars(stmt).unique().all())

    @staticmethod
    def get_shipments_count(db: Session, route_id: int) -> int:
        """
        Counts the total number of shipments assigned to a route.
        """
        stmt = (
            select(func.count(RouteShipment.id))
            .where(RouteShipment.route_id == route_id)
        )
        return db.scalar(stmt) or 0


route_repository = RouteRepository()
