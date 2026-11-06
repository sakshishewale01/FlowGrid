"""Persistence operations for inventory movement history."""

from datetime import datetime
from typing import List

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.inventory_movement import InventoryMovement


class InventoryMovementRepository:
    @staticmethod
    def list_for_inventory(
        db: Session, inventory_id: int, since: datetime | None = None
    ) -> List[InventoryMovement]:
        statement = select(InventoryMovement).where(
            InventoryMovement.inventory_id == inventory_id
        )
        if since is not None:
            statement = statement.where(InventoryMovement.created_at >= since)
        statement = statement.order_by(InventoryMovement.created_at.asc(), InventoryMovement.id.asc())
        return list(db.scalars(statement).all())


inventory_movement_repository = InventoryMovementRepository()
