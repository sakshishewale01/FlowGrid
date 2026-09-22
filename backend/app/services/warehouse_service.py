"""
Warehouse Service
=================
Business logic layer managing warehouse validation, lifecycle rules,
and coordination with the repository.
"""

from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.warehouse import Warehouse
from app.models.shipment import Shipment, ShipmentStatus
from app.repositories.warehouse_repository import warehouse_repository
from app.schemas.warehouse import WarehouseCreate, WarehouseUpdate


class WarehouseService:
    """
    Business service for warehouse management.
    """

    def __init__(self, repository=warehouse_repository):
        self.repository = repository

    def _validate_warehouse_deactivation(self, db: Session, warehouse: Warehouse) -> None:
        """
        Ensures a warehouse cannot be deactivated or deleted if it contains positive inventory stock
        or is linked to active shipments.
        """
        if warehouse.inventories:
            total_stock = sum(inv.quantity for inv in warehouse.inventories)
            if total_stock > 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot deactivate warehouse '{warehouse.name}' with positive inventory balance ({total_stock} units)",
                )

        active_shipments_count = db.query(Shipment).filter(
            Shipment.origin_warehouse_id == warehouse.id,
            Shipment.status.in_([
                ShipmentStatus.CREATED,
                ShipmentStatus.CONFIRMED,
                ShipmentStatus.ASSIGNED,
                ShipmentStatus.PICKED_UP,
                ShipmentStatus.IN_TRANSIT,
                ShipmentStatus.OUT_FOR_DELIVERY,
            ]),
        ).count()
        if active_shipments_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot deactivate warehouse '{warehouse.name}' with {active_shipments_count} active shipment(s)",
            )

    def create_warehouse(self, db: Session, payload: WarehouseCreate) -> Warehouse:
        """
        Validates and creates a new warehouse record.
        """
        warehouse = Warehouse(
            name=payload.name.strip(),
            location=payload.location.strip(),
            address=payload.address.strip(),
            capacity=payload.capacity,
            is_active=payload.is_active,
        )
        return self.repository.create(db, warehouse)

    def get_warehouse(self, db: Session, warehouse_id: int) -> Warehouse:
        """
        Retrieves a warehouse by ID, raising HTTP 404 if it does not exist.
        """
        warehouse = self.repository.get_by_id(db, warehouse_id)
        if not warehouse:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Warehouse with ID {warehouse_id} was not found",
            )
        return warehouse

    def list_warehouses(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
    ) -> List[Warehouse]:
        """
        Retrieves a list of warehouses with optional pagination and active-status filtering.
        """
        return self.repository.get_all(
            db,
            skip=skip,
            limit=limit,
            is_active=is_active,
        )

    def update_warehouse(
        self,
        db: Session,
        warehouse_id: int,
        payload: WarehouseUpdate,
    ) -> Warehouse:
        """
        Updates an existing warehouse with non-empty fields from payload.
        Raises HTTP 404 if the warehouse does not exist.
        """
        warehouse = self.get_warehouse(db, warehouse_id)

        update_data = payload.model_dump(exclude_unset=True)

        if update_data.get("is_active") is False and warehouse.is_active:
            self._validate_warehouse_deactivation(db, warehouse)

        # Clean string inputs if supplied
        for str_field in ("name", "location", "address"):
            if str_field in update_data and update_data[str_field] is not None:
                update_data[str_field] = update_data[str_field].strip()

        if update_data:
            return self.repository.update(db, warehouse, update_data)
        return warehouse

    def delete_warehouse(self, db: Session, warehouse_id: int) -> Warehouse:
        """
        Soft-deletes a warehouse by setting `is_active = False`.
        Raises HTTP 404 if the warehouse does not exist.
        """
        warehouse = self.get_warehouse(db, warehouse_id)
        self._validate_warehouse_deactivation(db, warehouse)
        return self.repository.soft_delete(db, warehouse)


warehouse_service = WarehouseService()
