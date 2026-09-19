"""
Inventory Repository
====================
Encapsulates all database persistence and query operations for the Inventory model.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.inventory import Inventory


class InventoryRepository:
    """
    Data access layer for Inventory stock records.
    """

    @staticmethod
    def get_by_id(db: Session, inventory_id: int) -> Optional[Inventory]:
        """
        Retrieves a single inventory record by ID with eager loading of warehouse and product.
        """
        stmt = (
            select(Inventory)
            .options(
                joinedload(Inventory.warehouse),
                joinedload(Inventory.product),
            )
            .where(Inventory.id == inventory_id)
        )
        return db.scalars(stmt).first()

    @staticmethod
    def get_by_warehouse_and_product(
        db: Session,
        warehouse_id: int,
        product_id: int,
    ) -> Optional[Inventory]:
        """
        Retrieves an inventory record for a specific warehouse and product pairing.
        """
        stmt = select(Inventory).where(
            Inventory.warehouse_id == warehouse_id,
            Inventory.product_id == product_id,
        )
        return db.scalars(stmt).first()

    @staticmethod
    def get_all(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        warehouse_id: Optional[int] = None,
        product_id: Optional[int] = None,
    ) -> List[Inventory]:
        """
        Retrieves a paginated list of inventory records with optional filtering
        by warehouse_id and/or product_id.
        """
        stmt = (
            select(Inventory)
            .options(
                joinedload(Inventory.warehouse),
                joinedload(Inventory.product),
            )
        )
        if warehouse_id is not None:
            stmt = stmt.where(Inventory.warehouse_id == warehouse_id)
        if product_id is not None:
            stmt = stmt.where(Inventory.product_id == product_id)

        stmt = stmt.offset(skip).limit(limit).order_by(Inventory.id.asc())
        return list(db.scalars(stmt).all())

    @staticmethod
    def create(db: Session, inventory: Inventory) -> Inventory:
        """
        Persists a new inventory record into the database.
        """
        db.add(inventory)
        db.commit()
        db.refresh(inventory)
        return inventory

    @staticmethod
    def update(
        db: Session,
        inventory: Inventory,
        update_data: Dict[str, Any],
    ) -> Inventory:
        """
        Applies updates to an existing inventory entity.
        """
        for field, value in update_data.items():
            setattr(inventory, field, value)
        db.commit()
        db.refresh(inventory)
        return inventory

    @staticmethod
    def delete(db: Session, inventory: Inventory) -> None:
        """
        Permanently deletes an inventory record from the database.
        """
        db.delete(inventory)
        db.commit()


inventory_repository = InventoryRepository()
