"""
Product Repository
==================
Encapsulates all database persistence and query operations for the Product model.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.product import Product


class ProductRepository:
    """
    Data access layer for Product catalog records.
    """

    @staticmethod
    def get_by_id(db: Session, product_id: int) -> Optional[Product]:
        """
        Retrieves a single product by primary key ID.
        """
        return db.get(Product, product_id)

    @staticmethod
    def get_by_sku(db: Session, sku: str) -> Optional[Product]:
        """
        Retrieves a product by SKU using consistent normalized uppercase comparison.
        """
        normalized_sku = sku.strip().upper()
        stmt = select(Product).where(
            func.upper(func.trim(Product.sku)) == normalized_sku
        )
        return db.scalars(stmt).first()

    @staticmethod
    def get_all(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
    ) -> List[Product]:
        """
        Retrieves a paginated list of products with optional active status filter.
        """
        stmt = select(Product)
        if is_active is not None:
            stmt = stmt.where(Product.is_active == is_active)
        stmt = stmt.offset(skip).limit(limit).order_by(Product.id.asc())
        return list(db.scalars(stmt).all())

    @staticmethod
    def create(db: Session, product: Product) -> Product:
        """
        Persists a new product entity in the database.
        """
        db.add(product)
        db.commit()
        db.refresh(product)
        return product

    @staticmethod
    def update(
        db: Session,
        product: Product,
        update_data: Dict[str, Any],
    ) -> Product:
        """
        Applies partial or full updates to an existing product entity.
        """
        for field, value in update_data.items():
            setattr(product, field, value)
        db.commit()
        db.refresh(product)
        return product

    @staticmethod
    def soft_delete(db: Session, product: Product) -> Product:
        """
        Soft-deletes a product by setting `is_active = False`.
        """
        product.is_active = False
        db.commit()
        db.refresh(product)
        return product


product_repository = ProductRepository()
