"""
Inventory Service
=================
Business logic layer managing inventory balances, relational validation with
warehouses and products, duplicate constraint enforcement, and repository calls.
"""

from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.inventory import Inventory
from app.repositories.inventory_repository import inventory_repository
from app.repositories.warehouse_repository import warehouse_repository
from app.repositories.product_repository import product_repository
from app.schemas.inventory import InventoryCreate, InventoryUpdate


class InventoryService:
    """
    Business service for inventory stock management.
    """

    def __init__(
        self,
        repository=inventory_repository,
        warehouse_repo=warehouse_repository,
        product_repo=product_repository,
    ):
        self.repository = repository
        self.warehouse_repo = warehouse_repo
        self.product_repo = product_repo

    def create_inventory(
        self,
        db: Session,
        payload: InventoryCreate,
    ) -> Inventory:
        """
        Validates warehouse and product existence, active status, and non-duplicate
        pairing before creating a new inventory record.
        """
        # 1. Validate Warehouse exists and is active
        warehouse = self.warehouse_repo.get_by_id(db, payload.warehouse_id)
        if not warehouse:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Warehouse with ID {payload.warehouse_id} does not exist",
            )
        if not warehouse.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Warehouse '{warehouse.name}' (ID {payload.warehouse_id}) is inactive",
            )

        # 2. Validate Product exists and is active
        product = self.product_repo.get_by_id(db, payload.product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product with ID {payload.product_id} does not exist",
            )
        if not product.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product '{product.name}' (ID {payload.product_id}) is inactive",
            )

        # 3. Check for duplicate warehouse-product combination
        existing = self.repository.get_by_warehouse_and_product(
            db,
            payload.warehouse_id,
            payload.product_id,
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"An inventory record for product '{product.name}' (ID {payload.product_id}) "
                    f"at warehouse '{warehouse.name}' (ID {payload.warehouse_id}) already exists"
                ),
            )

        # 4. Check warehouse capacity limit
        existing_items = self.repository.get_all(db, warehouse_id=payload.warehouse_id, limit=10000)
        current_total = sum(item.quantity for item in existing_items)
        if current_total + payload.quantity > warehouse.capacity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Total warehouse inventory ({current_total + payload.quantity} units) would exceed warehouse capacity ({warehouse.capacity} units)",
            )

        # 5. Create and persist the inventory record
        inventory = Inventory(
            warehouse_id=payload.warehouse_id,
            product_id=payload.product_id,
            quantity=payload.quantity,
            reorder_level=payload.reorder_level,
        )
        return self.repository.create(db, inventory)

    def get_inventory(self, db: Session, inventory_id: int) -> Inventory:
        """
        Retrieves a single inventory record by ID, raising HTTP 404 if not found.
        """
        inventory = self.repository.get_by_id(db, inventory_id)
        if not inventory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Inventory record with ID {inventory_id} was not found",
            )
        return inventory

    def list_inventory(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        warehouse_id: Optional[int] = None,
        product_id: Optional[int] = None,
    ) -> List[Inventory]:
        """
        Retrieves a paginated list of inventory records with optional warehouse and product filters.
        """
        return self.repository.get_all(
            db,
            skip=skip,
            limit=limit,
            warehouse_id=warehouse_id,
            product_id=product_id,
        )

    def update_inventory(
        self,
        db: Session,
        inventory_id: int,
        payload: InventoryUpdate,
    ) -> Inventory:
        """
        Updates stock quantity and/or reorder level of an existing inventory record.
        Raises HTTP 404 if not found.
        """
        inventory = self.get_inventory(db, inventory_id)

        update_data = payload.model_dump(exclude_unset=True)

        if "quantity" in update_data and update_data["quantity"] is not None:
            new_qty = update_data["quantity"]
            warehouse = self.warehouse_repo.get_by_id(db, inventory.warehouse_id)
            if warehouse:
                existing_items = self.repository.get_all(db, warehouse_id=inventory.warehouse_id, limit=10000)
                current_total = sum(item.quantity for item in existing_items if item.id != inventory_id)
                if current_total + new_qty > warehouse.capacity:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Total warehouse inventory ({current_total + new_qty} units) would exceed warehouse capacity ({warehouse.capacity} units)",
                    )

        if update_data:
            inventory = self.repository.update(db, inventory, update_data)
        return inventory

    def delete_inventory(
        self,
        db: Session,
        inventory_id: int,
    ) -> Dict[str, Any]:
        """
        Deletes an inventory record from the database.
        Note: The Inventory model does not have an `is_active` field. Hard deletion
        is performed safely with ADMIN authorization.
        Raises HTTP 404 if not found.
        """
        inventory = self.get_inventory(db, inventory_id)
        self.repository.delete(db, inventory)
        return {
            "message": f"Inventory record with ID {inventory_id} was deleted successfully",
            "id": inventory_id,
        }


inventory_service = InventoryService()
