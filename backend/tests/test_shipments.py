"""
FlowGrid - Shipment Management Backend Tests
===========================================
Comprehensive test suite validating:
- Shipment CRUD operations with layered architecture (Repository, Service, Endpoint).
- Unique tracking number generation and custom tracking number uniqueness.
- Role-Based Access Control (RBAC):
  * Create: ADMIN, MANAGER allowed; DRIVER, VIEWER forbidden (403).
  * Read: All authenticated roles allowed (by ID and by tracking number).
  * Update: ADMIN, MANAGER allowed; DRIVER, VIEWER forbidden (403).
  * Status Lifecycle Updates: ADMIN, MANAGER allowed; DRIVER, VIEWER forbidden (403).
  * Delete: ADMIN only; MANAGER, DRIVER, VIEWER forbidden (403).
- Shipment state machine lifecycle transitions (CREATED -> CONFIRMED -> ASSIGNED -> ... -> DELIVERED).
- Rejection of invalid status transitions (HTTP 400).
- Prevention of unsafe modifications after delivery.
- Soft deletion preserving shipment historical records.
- 404 Not Found handling.
"""

import pytest
from decimal import Decimal
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.db.base import Base
from app.main import app

# ------------------------------------------------------------------------------
# Test Database Setup (Isolated in-memory SQLite with StaticPool)
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
    return get_auth_headers_for_role(client, "admin_ship@flowgrid.io", "ADMIN")


@pytest.fixture
def manager_headers(client):
    return get_auth_headers_for_role(client, "manager_ship@flowgrid.io", "MANAGER")


@pytest.fixture
def driver_headers(client):
    return get_auth_headers_for_role(client, "driver_ship@flowgrid.io", "DRIVER")


@pytest.fixture
def viewer_headers(client):
    return get_auth_headers_for_role(client, "viewer_ship@flowgrid.io", "VIEWER")


@pytest.fixture
def active_warehouse(client, admin_headers):
    res = client.post(
        "/api/v1/warehouses",
        json={
            "name": "Austin Fulfillment Depot",
            "location": "Austin, TX",
            "address": "1000 Tech Ridge Blvd, Austin, TX 78753",
            "capacity": 55000,
            "is_active": True,
        },
        headers=admin_headers,
    )
    return res.json()


SAMPLE_SHIPMENT = {
    "destination_address": "742 Evergreen Terrace",
    "destination_city": "Springfield",
    "destination_state": "IL",
    "destination_postal_code": "62704",
    "total_weight_kg": 150.50,
    "total_volume_cbm": 1.25,
}


# ------------------------------------------------------------------------------
# 1. Create Shipment Tests
# ------------------------------------------------------------------------------
def test_create_shipment_as_admin(client, admin_headers, active_warehouse):
    payload = {
        **SAMPLE_SHIPMENT,
        "origin_warehouse_id": active_warehouse["id"],
    }
    response = client.post("/api/v1/shipments", json=payload, headers=admin_headers)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["status"] == "CREATED"
    assert data["tracking_number"].startswith("FG-")
    assert data["origin_warehouse_id"] == active_warehouse["id"]
    assert data["destination_city"] == "Springfield"
    assert Decimal(str(data["total_weight_kg"])) == Decimal("150.50")
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data


def test_create_shipment_as_manager(client, manager_headers):
    payload = {
        "destination_address": "1200 Ocean Drive",
        "destination_city": "Miami",
        "destination_state": "FL",
        "destination_postal_code": "33139",
    }
    response = client.post("/api/v1/shipments", json=payload, headers=manager_headers)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["status"] == "CREATED"
    assert response.json()["destination_city"] == "Miami"


def test_create_shipment_with_custom_tracking_number(client, admin_headers):
    payload = {
        **SAMPLE_SHIPMENT,
        "tracking_number": "FG-2026-CUSTOM-01",
    }
    response = client.post("/api/v1/shipments", json=payload, headers=admin_headers)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["tracking_number"] == "FG-2026-CUSTOM-01"


def test_create_shipment_duplicate_tracking_number(client, admin_headers):
    payload = {
        **SAMPLE_SHIPMENT,
        "tracking_number": "FG-UNIQUE-TRACK-99",
    }
    res1 = client.post("/api/v1/shipments", json=payload, headers=admin_headers)
    assert res1.status_code == status.HTTP_201_CREATED

    # Attempt duplicate (case variation)
    payload2 = {
        **SAMPLE_SHIPMENT,
        "tracking_number": "fg-unique-track-99",
    }
    res2 = client.post("/api/v1/shipments", json=payload2, headers=admin_headers)
    assert res2.status_code == status.HTTP_400_BAD_REQUEST
    assert "already registered" in res2.json()["detail"]


def test_create_shipment_rejected_for_driver(client, driver_headers):
    response = client.post("/api/v1/shipments", json=SAMPLE_SHIPMENT, headers=driver_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "Access forbidden" in response.json()["detail"]


def test_create_shipment_rejected_for_viewer(client, viewer_headers):
    response = client.post("/api/v1/shipments", json=SAMPLE_SHIPMENT, headers=viewer_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_create_shipment_unauthenticated(client):
    response = client.post("/api/v1/shipments", json=SAMPLE_SHIPMENT)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_shipment_invalid_warehouse(client, admin_headers):
    payload = {
        **SAMPLE_SHIPMENT,
        "origin_warehouse_id": 99999,
    }
    response = client.post("/api/v1/shipments", json=payload, headers=admin_headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Warehouse with ID 99999 does not exist" in response.json()["detail"]


# ------------------------------------------------------------------------------
# 2. Get Shipments Tests (All, Filters, By ID, By Tracking)
# ------------------------------------------------------------------------------
def test_get_all_shipments_and_filters(client, admin_headers, viewer_headers):
    client.post(
        "/api/v1/shipments",
        json={**SAMPLE_SHIPMENT, "tracking_number": "FG-FILTER-01"},
        headers=admin_headers,
    )
    client.post(
        "/api/v1/shipments",
        json={**SAMPLE_SHIPMENT, "tracking_number": "FG-FILTER-02"},
        headers=admin_headers,
    )

    # Viewer lists shipments
    res = client.get("/api/v1/shipments", headers=viewer_headers)
    assert res.status_code == status.HTTP_200_OK
    assert len(res.json()) == 2

    # Filter status=CREATED
    status_res = client.get("/api/v1/shipments?status=CREATED", headers=viewer_headers)
    assert status_res.status_code == status.HTTP_200_OK
    assert len(status_res.json()) == 2

    # Filter tracking_number
    trk_res = client.get("/api/v1/shipments?tracking_number=FILTER-01", headers=viewer_headers)
    assert trk_res.status_code == status.HTTP_200_OK
    assert len(trk_res.json()) == 1
    assert trk_res.json()[0]["tracking_number"] == "FG-FILTER-01"

    # Pagination
    limit_res = client.get("/api/v1/shipments?limit=1", headers=viewer_headers)
    assert limit_res.status_code == status.HTTP_200_OK
    assert len(limit_res.json()) == 1


def test_get_shipment_by_id(client, admin_headers, driver_headers):
    create_res = client.post("/api/v1/shipments", json=SAMPLE_SHIPMENT, headers=admin_headers)
    ship_id = create_res.json()["id"]

    res = client.get(f"/api/v1/shipments/{ship_id}", headers=driver_headers)
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["id"] == ship_id
    assert res.json()["destination_city"] == "Springfield"


def test_get_shipment_by_tracking_number(client, admin_headers, viewer_headers):
    create_res = client.post(
        "/api/v1/shipments",
        json={**SAMPLE_SHIPMENT, "tracking_number": "FG-TRACK-FIND-ME"},
        headers=admin_headers,
    )
    tracking = create_res.json()["tracking_number"]

    res = client.get(f"/api/v1/shipments/tracking/{tracking}", headers=viewer_headers)
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["tracking_number"] == "FG-TRACK-FIND-ME"


def test_get_shipment_not_found(client, viewer_headers):
    # ID not found
    res1 = client.get("/api/v1/shipments/99999", headers=viewer_headers)
    assert res1.status_code == status.HTTP_404_NOT_FOUND

    # Tracking not found
    res2 = client.get("/api/v1/shipments/tracking/FG-DOES-NOT-EXIST", headers=viewer_headers)
    assert res2.status_code == status.HTTP_404_NOT_FOUND


# ------------------------------------------------------------------------------
# 3. Update Shipment Tests
# ------------------------------------------------------------------------------
def test_update_shipment_as_admin_and_manager(client, admin_headers, manager_headers):
    create_res = client.post("/api/v1/shipments", json=SAMPLE_SHIPMENT, headers=admin_headers)
    ship_id = create_res.json()["id"]

    # Admin updates
    update_res = client.put(
        f"/api/v1/shipments/{ship_id}",
        json={"destination_address": "800 New Road", "destination_city": "Chicago"},
        headers=admin_headers,
    )
    assert update_res.status_code == status.HTTP_200_OK
    assert update_res.json()["destination_address"] == "800 New Road"
    assert update_res.json()["destination_city"] == "Chicago"

    # Manager updates
    patch_res = client.patch(
        f"/api/v1/shipments/{ship_id}",
        json={"total_weight_kg": 250.00},
        headers=manager_headers,
    )
    assert patch_res.status_code == status.HTTP_200_OK
    assert Decimal(str(patch_res.json()["total_weight_kg"])) == Decimal("250.00")


def test_update_shipment_rejected_for_driver_and_viewer(client, admin_headers, driver_headers, viewer_headers):
    create_res = client.post("/api/v1/shipments", json=SAMPLE_SHIPMENT, headers=admin_headers)
    ship_id = create_res.json()["id"]

    assert client.put(f"/api/v1/shipments/{ship_id}", json={"destination_city": "Hack"}, headers=driver_headers).status_code == status.HTTP_403_FORBIDDEN
    assert client.put(f"/api/v1/shipments/{ship_id}", json={"destination_city": "Hack"}, headers=viewer_headers).status_code == status.HTTP_403_FORBIDDEN


# ------------------------------------------------------------------------------
# 4. Shipment State Machine Lifecycle Tests
# ------------------------------------------------------------------------------
def test_valid_shipment_status_lifecycle(client, admin_headers, manager_headers):
    create_res = client.post("/api/v1/shipments", json=SAMPLE_SHIPMENT, headers=admin_headers)
    ship_id = create_res.json()["id"]
    assert create_res.json()["status"] == "CREATED"

    # 1. CREATED -> CONFIRMED
    res = client.patch(f"/api/v1/shipments/{ship_id}/status", json={"status": "CONFIRMED"}, headers=manager_headers)
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["status"] == "CONFIRMED"

    # 2. CONFIRMED -> ASSIGNED
    res = client.patch(f"/api/v1/shipments/{ship_id}/status", json={"status": "ASSIGNED"}, headers=admin_headers)
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["status"] == "ASSIGNED"

    # 3. ASSIGNED -> PICKED_UP
    res = client.patch(f"/api/v1/shipments/{ship_id}/status", json={"status": "PICKED_UP"}, headers=manager_headers)
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["status"] == "PICKED_UP"

    # 4. PICKED_UP -> IN_TRANSIT
    res = client.patch(f"/api/v1/shipments/{ship_id}/status", json={"status": "IN_TRANSIT"}, headers=admin_headers)
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["status"] == "IN_TRANSIT"

    # 5. IN_TRANSIT -> OUT_FOR_DELIVERY
    res = client.patch(f"/api/v1/shipments/{ship_id}/status", json={"status": "OUT_FOR_DELIVERY"}, headers=manager_headers)
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["status"] == "OUT_FOR_DELIVERY"

    # 6. OUT_FOR_DELIVERY -> DELIVERED (Terminal state)
    res = client.patch(f"/api/v1/shipments/{ship_id}/status", json={"status": "DELIVERED"}, headers=admin_headers)
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["status"] == "DELIVERED"
    assert res.json()["delivered_at"] is not None


def test_exception_status_lifecycle_transitions(client, admin_headers):
    # Test Cancellation from CREATED
    s1 = client.post("/api/v1/shipments", json=SAMPLE_SHIPMENT, headers=admin_headers).json()
    res_cancel = client.patch(f"/api/v1/shipments/{s1['id']}/status", json={"status": "CANCELLED"}, headers=admin_headers)
    assert res_cancel.status_code == status.HTTP_200_OK
    assert res_cancel.json()["status"] == "CANCELLED"

    # Test FAILED and RETURNED lifecycle
    s2 = client.post("/api/v1/shipments", json=SAMPLE_SHIPMENT, headers=admin_headers).json()
    client.patch(f"/api/v1/shipments/{s2['id']}/status", json={"status": "CONFIRMED"}, headers=admin_headers)
    client.patch(f"/api/v1/shipments/{s2['id']}/status", json={"status": "ASSIGNED"}, headers=admin_headers)
    client.patch(f"/api/v1/shipments/{s2['id']}/status", json={"status": "PICKED_UP"}, headers=admin_headers)
    client.patch(f"/api/v1/shipments/{s2['id']}/status", json={"status": "IN_TRANSIT"}, headers=admin_headers)
    client.patch(f"/api/v1/shipments/{s2['id']}/status", json={"status": "OUT_FOR_DELIVERY"}, headers=admin_headers)

    # Transition OUT_FOR_DELIVERY -> FAILED
    fail_res = client.patch(f"/api/v1/shipments/{s2['id']}/status", json={"status": "FAILED"}, headers=admin_headers)
    assert fail_res.status_code == status.HTTP_200_OK
    assert fail_res.json()["status"] == "FAILED"

    # Transition FAILED -> RETURNED (Terminal state)
    ret_res = client.patch(f"/api/v1/shipments/{s2['id']}/status", json={"status": "RETURNED"}, headers=admin_headers)
    assert ret_res.status_code == status.HTTP_200_OK
    assert ret_res.json()["status"] == "RETURNED"


def test_invalid_status_transitions_rejected(client, admin_headers):
    s = client.post("/api/v1/shipments", json=SAMPLE_SHIPMENT, headers=admin_headers).json()

    # Illegal jump: CREATED -> DELIVERED
    jump_res = client.patch(f"/api/v1/shipments/{s['id']}/status", json={"status": "DELIVERED"}, headers=admin_headers)
    assert jump_res.status_code == status.HTTP_400_BAD_REQUEST
    assert "Illegal status transition" in jump_res.json()["detail"]

    # Cancel the shipment
    client.patch(f"/api/v1/shipments/{s['id']}/status", json={"status": "CANCELLED"}, headers=admin_headers)

    # Attempt transition out of terminal CANCELLED state
    terminal_res = client.patch(f"/api/v1/shipments/{s['id']}/status", json={"status": "CONFIRMED"}, headers=admin_headers)
    assert terminal_res.status_code == status.HTTP_400_BAD_REQUEST
    assert "Illegal status transition" in terminal_res.json()["detail"]


def test_prevent_update_after_delivered(client, admin_headers):
    s = client.post("/api/v1/shipments", json=SAMPLE_SHIPMENT, headers=admin_headers).json()
    ship_id = s["id"]

    # Progress to DELIVERED
    for st in ("CONFIRMED", "ASSIGNED", "PICKED_UP", "IN_TRANSIT", "OUT_FOR_DELIVERY", "DELIVERED"):
        client.patch(f"/api/v1/shipments/{ship_id}/status", json={"status": st}, headers=admin_headers)

    # Attempt updating delivery details on a delivered shipment
    res = client.put(f"/api/v1/shipments/{ship_id}", json={"destination_city": "Denver"}, headers=admin_headers)
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert "Cannot modify shipment details after successful delivery" in res.json()["detail"]


# ------------------------------------------------------------------------------
# 5. Delete Shipment Tests (Soft Delete)
# ------------------------------------------------------------------------------
def test_delete_shipment_as_admin_soft_deletes(client, admin_headers, viewer_headers):
    s = client.post("/api/v1/shipments", json=SAMPLE_SHIPMENT, headers=admin_headers).json()
    ship_id = s["id"]

    del_res = client.delete(f"/api/v1/shipments/{ship_id}", headers=admin_headers)
    assert del_res.status_code == status.HTTP_200_OK
    assert del_res.json()["is_active"] is False

    # Historical record still accessible via GET, marked inactive
    get_res = client.get(f"/api/v1/shipments/{ship_id}", headers=viewer_headers)
    assert get_res.status_code == status.HTTP_200_OK
    assert get_res.json()["is_active"] is False


def test_delete_shipment_rejected_for_manager(client, admin_headers, manager_headers):
    s = client.post("/api/v1/shipments", json=SAMPLE_SHIPMENT, headers=admin_headers).json()
    del_res = client.delete(f"/api/v1/shipments/{s['id']}", headers=manager_headers)
    assert del_res.status_code == status.HTTP_403_FORBIDDEN


def test_delete_shipment_rejected_for_driver_and_viewer(client, admin_headers, driver_headers, viewer_headers):
    s = client.post("/api/v1/shipments", json=SAMPLE_SHIPMENT, headers=admin_headers).json()
    assert client.delete(f"/api/v1/shipments/{s['id']}", headers=driver_headers).status_code == status.HTTP_403_FORBIDDEN
    assert client.delete(f"/api/v1/shipments/{s['id']}", headers=viewer_headers).status_code == status.HTTP_403_FORBIDDEN


def test_delete_shipment_not_found(client, admin_headers):
    res = client.delete("/api/v1/shipments/99999", headers=admin_headers)
    assert res.status_code == status.HTTP_404_NOT_FOUND
