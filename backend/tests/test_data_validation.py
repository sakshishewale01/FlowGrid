"""
FlowGrid - Data Quality & Validation Tests (Phase 20)
===================================================
Comprehensive test suite validating data quality and domain constraints across:
1. Shipment: Sanitization, weight/volume limits, dates, driver/vehicle eligibility & capacity.
2. Warehouse: Sanitization, capacity bounds, deactivation guards (inventory & active shipments).
3. Inventory: Bounds on quantity/reorder_level, warehouse capacity overflow on create & update.
4. Driver: Sanitization, valid statuses, user role verification (rejecting VIEWER).
5. Vehicle: Sanitization, capacity bounds, status validation, maintenance/decommission guards during active dispatch.
"""

from decimal import Decimal
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.db.base import Base
from app.main import app

# ------------------------------------------------------------------------------
# Test Database Setup
# ------------------------------------------------------------------------------
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client():
    return TestClient(app)


def get_auth_headers_for_role(client: TestClient, email: str, role: str) -> dict:
    password = "SecurePassword2026!"
    client.post(
        "/api/v1/auth/register",
        json={
            "name": f"{role.capitalize()} User",
            "email": email,
            "password": password,
            "role": role,
        },
    )
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(client):
    return get_auth_headers_for_role(client, "admin_val@flowgrid.io", "ADMIN")


@pytest.fixture
def manager_headers(client):
    return get_auth_headers_for_role(client, "manager_val@flowgrid.io", "MANAGER")


@pytest.fixture
def driver_user_id(client):
    res = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Eligible Driver",
            "email": "driver_eligible@flowgrid.io",
            "password": "SecurePassword2026!",
            "role": "DRIVER",
        },
    )
    return res.json()["id"]


@pytest.fixture
def viewer_user_id(client):
    res = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Readonly Viewer",
            "email": "viewer_ro@flowgrid.io",
            "password": "SecurePassword2026!",
            "role": "VIEWER",
        },
    )
    return res.json()["id"]


@pytest.fixture
def standard_warehouse(client, admin_headers):
    res = client.post(
        "/api/v1/warehouses",
        json={
            "name": "Central Hub",
            "location": "Chicago, IL",
            "address": "1000 Hub Way, Chicago, IL 60601",
            "capacity": 5000,
            "is_active": True,
        },
        headers=admin_headers,
    )
    return res.json()


@pytest.fixture
def standard_product(client, admin_headers):
    res = client.post(
        "/api/v1/products",
        json={
            "name": "Heavy Duty Box",
            "sku": "BOX-HD-001",
            "description": "Reinforced shipping carton",
            "unit_price": 5.99,
            "is_active": True,
        },
        headers=admin_headers,
    )
    return res.json()


@pytest.fixture
def standard_driver(client, admin_headers, driver_user_id):
    res = client.post(
        "/api/v1/drivers",
        json={
            "user_id": driver_user_id,
            "license_number": "CDL-VAL-101",
            "phone_number": "+1-555-837-1928",
            "availability_status": "AVAILABLE",
        },
        headers=admin_headers,
    )
    return res.json()


@pytest.fixture
def standard_vehicle(client, admin_headers):
    res = client.post(
        "/api/v1/vehicles",
        json={
            "registration_number": "TRK-VAL-01",
            "vehicle_type": "Box Truck",
            "capacity": 5000.00,
            "status": "AVAILABLE",
        },
        headers=admin_headers,
    )
    return res.json()


# ==============================================================================
# 1. SHIPMENT DATA VALIDATION TESTS
# ==============================================================================

def test_shipment_whitespace_sanitization_rejected(client, admin_headers, standard_warehouse):
    # Blank or whitespace-only destination address should be rejected with 422
    payload = {
        "origin_warehouse_id": standard_warehouse["id"],
        "destination_address": "    ",
        "destination_city": "Chicago",
        "destination_state": "IL",
        "destination_postal_code": "60601",
    }
    res = client.post("/api/v1/shipments", json=payload, headers=admin_headers)
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_shipment_weight_and_volume_bounds(client, admin_headers, standard_warehouse):
    base_payload = {
        "origin_warehouse_id": standard_warehouse["id"],
        "destination_address": "123 Market St",
        "destination_city": "Chicago",
        "destination_state": "IL",
        "destination_postal_code": "60601",
    }

    # Negative weight
    res1 = client.post("/api/v1/shipments", json={**base_payload, "total_weight_kg": -10}, headers=admin_headers)
    assert res1.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Zero weight (gt=0)
    res2 = client.post("/api/v1/shipments", json={**base_payload, "total_weight_kg": 0}, headers=admin_headers)
    assert res2.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Weight exceeding 100,000 kg upper limit
    res3 = client.post("/api/v1/shipments", json={**base_payload, "total_weight_kg": 100001}, headers=admin_headers)
    assert res3.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Negative volume
    res4 = client.post("/api/v1/shipments", json={**base_payload, "total_volume_cbm": -1.5}, headers=admin_headers)
    assert res4.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Volume exceeding 1,000 cbm
    res5 = client.post("/api/v1/shipments", json={**base_payload, "total_volume_cbm": 1001}, headers=admin_headers)
    assert res5.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_shipment_scheduled_date_validation(client, admin_headers, standard_warehouse):
    # Year earlier than 2020 should fail
    payload = {
        "origin_warehouse_id": standard_warehouse["id"],
        "destination_address": "123 Market St",
        "destination_city": "Chicago",
        "destination_state": "IL",
        "destination_postal_code": "60601",
        "scheduled_pickup_at": "2018-05-12T10:00:00Z",
    }
    res = client.post("/api/v1/shipments", json=payload, headers=admin_headers)
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_shipment_weight_exceeding_vehicle_capacity_rejected(
    client, admin_headers, standard_warehouse, standard_driver, standard_vehicle
):
    # standard_vehicle capacity is 5000.00 kg. Total weight 5001.00 kg must be rejected with 400.
    payload = {
        "origin_warehouse_id": standard_warehouse["id"],
        "destination_address": "123 Market St",
        "destination_city": "Chicago",
        "destination_state": "IL",
        "destination_postal_code": "60601",
        "assigned_driver_id": standard_driver["id"],
        "assigned_vehicle_id": standard_vehicle["id"],
        "total_weight_kg": 5000.01,
    }
    res = client.post("/api/v1/shipments", json=payload, headers=admin_headers)
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert "exceeds vehicle carrying capacity" in res.json()["detail"]


def test_shipment_rejects_off_duty_or_suspended_driver(
    client, admin_headers, standard_warehouse, standard_driver
):
    # Update driver to OFF_DUTY
    client.put(
        f"/api/v1/drivers/{standard_driver['id']}",
        json={"availability_status": "OFF_DUTY"},
        headers=admin_headers,
    )

    payload = {
        "origin_warehouse_id": standard_warehouse["id"],
        "destination_address": "123 Market St",
        "destination_city": "Chicago",
        "destination_state": "IL",
        "destination_postal_code": "60601",
        "assigned_driver_id": standard_driver["id"],
    }
    res = client.post("/api/v1/shipments", json=payload, headers=admin_headers)
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert "OFF_DUTY" in res.json()["detail"]


def test_shipment_rejects_maintenance_or_decommissioned_vehicle(
    client, admin_headers, standard_warehouse, standard_vehicle
):
    # Update vehicle to MAINTENANCE
    client.put(
        f"/api/v1/vehicles/{standard_vehicle['id']}",
        json={"status": "MAINTENANCE"},
        headers=admin_headers,
    )

    payload = {
        "origin_warehouse_id": standard_warehouse["id"],
        "destination_address": "123 Market St",
        "destination_city": "Chicago",
        "destination_state": "IL",
        "destination_postal_code": "60601",
        "assigned_vehicle_id": standard_vehicle["id"],
    }
    res = client.post("/api/v1/shipments", json=payload, headers=admin_headers)
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert "MAINTENANCE" in res.json()["detail"]


def test_shipment_update_capacity_and_status_checks(
    client, admin_headers, standard_warehouse, standard_driver, standard_vehicle
):
    # Create valid shipment
    res = client.post(
        "/api/v1/shipments",
        json={
            "origin_warehouse_id": standard_warehouse["id"],
            "destination_address": "123 Market St",
            "destination_city": "Chicago",
            "destination_state": "IL",
            "destination_postal_code": "60601",
            "assigned_vehicle_id": standard_vehicle["id"],
            "total_weight_kg": 2000.00,
        },
        headers=admin_headers,
    )
    shipment_id = res.json()["id"]

    # Update total weight to exceed vehicle capacity
    update_res = client.put(
        f"/api/v1/shipments/{shipment_id}",
        json={"total_weight_kg": 6000.00},
        headers=admin_headers,
    )
    assert update_res.status_code == status.HTTP_400_BAD_REQUEST
    assert "exceeds vehicle carrying capacity" in update_res.json()["detail"]


# ==============================================================================
# 2. WAREHOUSE DATA VALIDATION TESTS
# ==============================================================================

def test_warehouse_whitespace_and_capacity_validation(client, admin_headers):
    # Blank name
    res1 = client.post(
        "/api/v1/warehouses",
        json={"name": "   ", "location": "Dallas, TX", "address": "100 Elm", "capacity": 1000},
        headers=admin_headers,
    )
    assert res1.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Capacity <= 0
    res2 = client.post(
        "/api/v1/warehouses",
        json={"name": "Dallas Hub", "location": "Dallas, TX", "address": "100 Elm", "capacity": 0},
        headers=admin_headers,
    )
    assert res2.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Capacity exceeding 50,000,000
    res3 = client.post(
        "/api/v1/warehouses",
        json={"name": "Mega Hub", "location": "Dallas, TX", "address": "100 Elm", "capacity": 50000001},
        headers=admin_headers,
    )
    assert res3.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_warehouse_deactivation_blocked_by_positive_inventory(
    client, admin_headers, standard_warehouse, standard_product
):
    # Add positive inventory
    client.post(
        "/api/v1/inventory",
        json={
            "warehouse_id": standard_warehouse["id"],
            "product_id": standard_product["id"],
            "quantity": 150,
            "reorder_level": 20,
        },
        headers=admin_headers,
    )

    # Attempt soft-delete
    del_res = client.delete(f"/api/v1/warehouses/{standard_warehouse['id']}", headers=admin_headers)
    assert del_res.status_code == status.HTTP_400_BAD_REQUEST
    assert "positive inventory balance" in del_res.json()["detail"]

    # Attempt updating is_active to False
    update_res = client.put(
        f"/api/v1/warehouses/{standard_warehouse['id']}",
        json={"is_active": False},
        headers=admin_headers,
    )
    assert update_res.status_code == status.HTTP_400_BAD_REQUEST
    assert "positive inventory balance" in update_res.json()["detail"]


def test_warehouse_deactivation_blocked_by_active_shipments(client, admin_headers):
    wh_res = client.post(
        "/api/v1/warehouses",
        json={"name": "Shipment WH", "location": "Miami, FL", "address": "100 Port Rd", "capacity": 2000},
        headers=admin_headers,
    )
    wh_id = wh_res.json()["id"]

    # Create active shipment originating from this warehouse
    client.post(
        "/api/v1/shipments",
        json={
            "origin_warehouse_id": wh_id,
            "destination_address": "500 Ocean Dr",
            "destination_city": "Miami",
            "destination_state": "FL",
            "destination_postal_code": "33139",
        },
        headers=admin_headers,
    )

    # Deletion must be blocked
    del_res = client.delete(f"/api/v1/warehouses/{wh_id}", headers=admin_headers)
    assert del_res.status_code == status.HTTP_400_BAD_REQUEST
    assert "active shipment" in del_res.json()["detail"]


# ==============================================================================
# 3. INVENTORY DATA VALIDATION TESTS
# ==============================================================================

def test_inventory_bounds_validation(client, admin_headers, standard_warehouse, standard_product):
    # Negative quantity
    res1 = client.post(
        "/api/v1/inventory",
        json={
            "warehouse_id": standard_warehouse["id"],
            "product_id": standard_product["id"],
            "quantity": -5,
        },
        headers=admin_headers,
    )
    assert res1.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Quantity exceeding 10,000,000
    res2 = client.post(
        "/api/v1/inventory",
        json={
            "warehouse_id": standard_warehouse["id"],
            "product_id": standard_product["id"],
            "quantity": 10000001,
        },
        headers=admin_headers,
    )
    assert res2.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Reorder level exceeding 1,000,000
    res3 = client.post(
        "/api/v1/inventory",
        json={
            "warehouse_id": standard_warehouse["id"],
            "product_id": standard_product["id"],
            "quantity": 10,
            "reorder_level": 1000001,
        },
        headers=admin_headers,
    )
    assert res3.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_inventory_warehouse_capacity_overflow(client, admin_headers, standard_warehouse, standard_product):
    # standard_warehouse has capacity 5000. Storing 5001 units must fail with 400.
    res = client.post(
        "/api/v1/inventory",
        json={
            "warehouse_id": standard_warehouse["id"],
            "product_id": standard_product["id"],
            "quantity": 5001,
        },
        headers=admin_headers,
    )
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert "exceed warehouse capacity" in res.json()["detail"]


def test_inventory_update_warehouse_capacity_overflow(
    client, admin_headers, standard_warehouse, standard_product
):
    # Create inventory with 4000 units
    inv = client.post(
        "/api/v1/inventory",
        json={
            "warehouse_id": standard_warehouse["id"],
            "product_id": standard_product["id"],
            "quantity": 4000,
        },
        headers=admin_headers,
    ).json()

    # Update to 5500 units (exceeding 5000)
    update_res = client.put(
        f"/api/v1/inventory/{inv['id']}",
        json={"quantity": 5500},
        headers=admin_headers,
    )
    assert update_res.status_code == status.HTTP_400_BAD_REQUEST
    assert "exceed warehouse capacity" in update_res.json()["detail"]


# ==============================================================================
# 4. DRIVER DATA VALIDATION TESTS
# ==============================================================================

def test_driver_status_and_string_validation(client, admin_headers, driver_user_id):
    # Invalid status
    res1 = client.post(
        "/api/v1/drivers",
        json={
            "user_id": driver_user_id,
            "license_number": "CDL-TEST-99",
            "phone_number": "+1-555-000-1111",
            "availability_status": "SUPER_AVAILABLE",
        },
        headers=admin_headers,
    )
    assert res1.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Blank license number
    res2 = client.post(
        "/api/v1/drivers",
        json={
            "user_id": driver_user_id,
            "license_number": "   ",
            "phone_number": "+1-555-000-1111",
        },
        headers=admin_headers,
    )
    assert res2.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_driver_user_role_validation(client, admin_headers, viewer_user_id):
    # Linking driver profile to a user with role VIEWER must be rejected with 400
    res = client.post(
        "/api/v1/drivers",
        json={
            "user_id": viewer_user_id,
            "license_number": "CDL-VIEWER-01",
            "phone_number": "+1-555-999-8888",
        },
        headers=admin_headers,
    )
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert "VIEWER" in res.json()["detail"]


# ==============================================================================
# 5. VEHICLE DATA VALIDATION TESTS
# ==============================================================================

def test_vehicle_status_and_capacity_bounds(client, admin_headers):
    # Invalid vehicle status
    res1 = client.post(
        "/api/v1/vehicles",
        json={
            "registration_number": "V-999",
            "vehicle_type": "Van",
            "capacity": 2000,
            "status": "DESTROYED",
        },
        headers=admin_headers,
    )
    assert res1.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Negative capacity
    res2 = client.post(
        "/api/v1/vehicles",
        json={
            "registration_number": "V-999",
            "vehicle_type": "Van",
            "capacity": -100,
        },
        headers=admin_headers,
    )
    assert res2.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Capacity exceeding 150,000 kg
    res3 = client.post(
        "/api/v1/vehicles",
        json={
            "registration_number": "V-999",
            "vehicle_type": "Van",
            "capacity": 150001,
        },
        headers=admin_headers,
    )
    assert res3.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_vehicle_maintenance_blocked_with_active_shipments(
    client, admin_headers, standard_warehouse, standard_vehicle
):
    # Assign vehicle to active shipment
    client.post(
        "/api/v1/shipments",
        json={
            "origin_warehouse_id": standard_warehouse["id"],
            "destination_address": "500 Ocean Dr",
            "destination_city": "Miami",
            "destination_state": "FL",
            "destination_postal_code": "33139",
            "assigned_vehicle_id": standard_vehicle["id"],
        },
        headers=admin_headers,
    )

    # Updating vehicle status to MAINTENANCE must be blocked
    up_res = client.put(
        f"/api/v1/vehicles/{standard_vehicle['id']}",
        json={"status": "MAINTENANCE"},
        headers=admin_headers,
    )
    assert up_res.status_code == status.HTTP_400_BAD_REQUEST
    assert "Cannot change vehicle status to MAINTENANCE" in up_res.json()["detail"]

    # Deleting vehicle must also be blocked
    del_res = client.delete(f"/api/v1/vehicles/{standard_vehicle['id']}", headers=admin_headers)
    assert del_res.status_code == status.HTTP_400_BAD_REQUEST
    assert "Cannot delete vehicle" in del_res.json()["detail"]
