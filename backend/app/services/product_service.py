"""
Product Service
===============
Business logic layer managing product catalog validation, duplicate SKU safety,
and coordination with the product repository.
"""

from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.product import Product
from app.repositories.product_repository import product_repository
from app.schemas.product import ProductCreate, ProductUpdate


class ProductService:
    """
    Business service for product catalog management.
    """

    def __init__(self, repository=product_repository):
        self.repository = repository

    def create_product(self, db: Session, payload: ProductCreate) -> Product:
        """
        Validates SKU uniqueness and creates a new product record.
        """
        normalized_sku = payload.sku.strip().upper()

        # Check for duplicate SKU safely
        existing = self.repository.get_by_sku(db, normalized_sku)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A product with SKU '{normalized_sku}' already exists",
            )

        product = Product(
            name=payload.name.strip(),
            sku=normalized_sku,
            description=payload.description.strip() if payload.description else None,
            unit_price=payload.unit_price,
            is_active=payload.is_active,
        )
        return self.repository.create(db, product)

    def get_product(self, db: Session, product_id: int) -> Product:
        """
        Retrieves a product by primary key ID, raising HTTP 404 if not found.
        """
        product = self.repository.get_by_id(db, product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {product_id} was not found",
            )
        return product

    def list_products(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
    ) -> List[Product]:
        """
        Retrieves a paginated list of products with optional active status filtering.
        """
        return self.repository.get_all(
            db,
            skip=skip,
            limit=limit,
            is_active=is_active,
        )

    def update_product(
        self,
        db: Session,
        product_id: int,
        payload: ProductUpdate,
    ) -> Product:
        """
        Updates an existing product with non-unset fields.
        Validates SKU uniqueness if SKU is being altered.
        Raises HTTP 404 if the product is not found.
        """
        product = self.get_product(db, product_id)

        update_data = payload.model_dump(exclude_unset=True)

        # Sanitize and validate SKU if present
        if "sku" in update_data and update_data["sku"] is not None:
            new_sku = update_data["sku"].strip().upper()
            if new_sku != product.sku.strip().upper():
                conflict = self.repository.get_by_sku(db, new_sku)
                if conflict and conflict.id != product_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"A product with SKU '{new_sku}' already exists",
                    )
            update_data["sku"] = new_sku

        # Sanitize string fields
        if "name" in update_data and update_data["name"] is not None:
            update_data["name"] = update_data["name"].strip()
        if "description" in update_data and update_data["description"] is not None:
            update_data["description"] = update_data["description"].strip()

        if update_data:
            return self.repository.update(db, product, update_data)
        return product

    def delete_product(self, db: Session, product_id: int) -> Product:
        """
        Soft-deletes a product by setting `is_active = False`.
        Raises HTTP 404 if the product does not exist.
        """
        product = self.get_product(db, product_id)
        return self.repository.soft_delete(db, product)


product_service = ProductService()
