"""
FlowGrid - Core Model Tests
===========================
Verifies that all Phase 3 SQLAlchemy models are registered, contain the
required table schemas, primary keys, and relationship mappings.
"""

from sqlalchemy import inspect
from app.db.base import Base
from app.models import (
    User,
    UserRole,
    Warehouse,
    Product,
    Inventory,
    Driver,
    Vehicle,
)


def test_models_registered_in_metadata():
    """
    Ensure all 6 core models are registered in Base.metadata.
    """
    expected_tables = {
        "users",
        "warehouses",
        "products",
        "inventories",
        "drivers",
        "vehicles",
    }
    registered_tables = set(Base.metadata.tables.keys())
    assert expected_tables.issubset(registered_tables)


def test_user_model_attributes():
    """
    Ensure User model contains required columns and enum choices.
    """
    mapper = inspect(User)
    column_names = {c.key for c in mapper.columns}
    required = {
        "id",
        "name",
        "email",
        "hashed_password",
        "role",
        "is_active",
        "created_at",
        "updated_at",
    }
    assert required.issubset(column_names)
    assert set(r.value for r in UserRole) == {"ADMIN", "MANAGER", "DRIVER", "VIEWER"}


def test_warehouse_model_attributes():
    """
    Ensure Warehouse model contains location, capacity, and active status.
    """
    mapper = inspect(Warehouse)
    column_names = {c.key for c in mapper.columns}
    required = {
        "id",
        "name",
        "location",
        "address",
        "capacity",
        "is_active",
        "created_at",
        "updated_at",
    }
    assert required.issubset(column_names)


def test_product_model_attributes():
    """
    Ensure Product model contains name, sku, unit_price, and timestamps.
    """
    mapper = inspect(Product)
    column_names = {c.key for c in mapper.columns}
    required = {
        "id",
        "name",
        "sku",
        "description",
        "unit_price",
        "is_active",
        "created_at",
        "updated_at",
    }
    assert required.issubset(column_names)


def test_inventory_foreign_keys_and_relationships():
    """
    Ensure Inventory model references both warehouses and products.
    """
    mapper = inspect(Inventory)
    column_names = {c.key for c in mapper.columns}
    assert {"id", "warehouse_id", "product_id", "quantity", "reorder_level", "updated_at"}.issubset(column_names)

    relationships = {r.key for r in mapper.relationships}
    assert "warehouse" in relationships
    assert "product" in relationships


def test_driver_model_attributes():
    """
    Ensure Driver model links to users and has license/availability fields.
    """
    mapper = inspect(Driver)
    column_names = {c.key for c in mapper.columns}
    required = {
        "id",
        "user_id",
        "license_number",
        "phone_number",
        "availability_status",
        "created_at",
        "updated_at",
    }
    assert required.issubset(column_names)
    assert "user" in {r.key for r in mapper.relationships}


def test_vehicle_model_attributes():
    """
    Ensure Vehicle model contains registration, type, capacity, and status.
    """
    mapper = inspect(Vehicle)
    column_names = {c.key for c in mapper.columns}
    required = {
        "id",
        "registration_number",
        "vehicle_type",
        "capacity",
        "status",
        "created_at",
        "updated_at",
    }
    assert required.issubset(column_names)
