"""
Warehouse Repository
====================
Encapsulates all database persistence operations for the Warehouse model.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.warehouse import Warehouse


class WarehouseRepository:
    """
    Data access layer for Warehouse records.
    """

    @staticmethod
    def get_by_id(db: Session, warehouse_id: int) -> Optional[Warehouse]:
        """
        Retrieves a single warehouse by its primary key ID.
        """
        return db.get(Warehouse, warehouse_id)

    @staticmethod
    def get_all(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
    ) -> List[Warehouse]:
        """
        Retrieves a paginated list of warehouses with optional active-status filtering.
        """
        stmt = select(Warehouse)
        if is_active is not None:
            stmt = stmt.where(Warehouse.is_active == is_active)
        stmt = stmt.offset(skip).limit(limit).order_by(Warehouse.id.asc())
        return list(db.scalars(stmt).all())

    @staticmethod
    def create(db: Session, warehouse: Warehouse) -> Warehouse:
        """
        Persists a new warehouse entity in the database.
        """
        db.add(warehouse)
        db.commit()
        db.refresh(warehouse)
        return warehouse

    @staticmethod
    def update(
        db: Session,
        warehouse: Warehouse,
        update_data: Dict[str, Any],
    ) -> Warehouse:
        """
        Updates fields on an existing warehouse entity.
        """
        for field, value in update_data.items():
            setattr(warehouse, field, value)
        db.commit()
        db.refresh(warehouse)
        return warehouse

    @staticmethod
    def soft_delete(db: Session, warehouse: Warehouse) -> Warehouse:
        """
        Performs a soft delete by marking the warehouse as inactive (`is_active = False`).
        """
        warehouse.is_active = False
        db.commit()
        db.refresh(warehouse)
        return warehouse


warehouse_repository = WarehouseRepository()
