"""
FlowGrid - Vehicle Fleet Management Tests
=========================================
Comprehensive test suite validating:
- Vehicle CRUD operations with layered architecture (Repository, Service, Endpoint).
- Unique registration number enforcement (case-insensitive).
- Capacity validation (capacity > 0).
- Role-Based Access Control (RBAC):
  * Create: ADMIN, MANAGER allowed; DRIVER, VIEWER forbidden (403).
  * Read: All authenticated roles allowed.
  * Update (PUT & PATCH): ADMIN, MANAGER allowed; DRIVER, VIEWER forbidden (403).
  * Delete: ADMIN only; MANAGER, DRIVER, VIEWER forbidden (403).
- 404 Not Found handling for non-existent vehicle entities.
- Filtering by status/is_active and pagination.
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
    return get_auth_headers_for_role(client, "admin_veh@flowgrid.io", "ADMIN")


@pytest.fixture
def manager_headers(client):
    return get_auth_headers_for_role(client, "manager_veh@flowgrid.io", "MANAGER")


@pytest.fixture
def driver_headers(client):
    return get_auth_headers_for_role(client, "driver_veh@flowgrid.io", "DRIVER")


@pytest.fixture
def viewer_headers(client):
    return get_auth_headers_for_role(client, "viewer_veh@flowgrid.io", "VIEWER")


SAMPLE_VEHICLE = {
    "registration_number": "TRK-TX-9001",
    "vehicle_type": "Heavy Semi-Trailer",
    "capacity": 22500.00,
    "status": "AVAILABLE",
}


# ------------------------------------------------------------------------------
# 1. Create Vehicle Tests
# ------------------------------------------------------------------------------
def test_create_vehicle_as_admin(client, admin_headers):
    response = client.post("/api/v1/vehicles", json=SAMPLE_VEHICLE, headers=admin_headers)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["registration_number"] == "TRK-TX-9001"
    assert data["vehicle_type"] == "Heavy Semi-Trailer"
    assert Decimal(str(data["capacity"])) == Decimal("22500.00")
    assert data["status"] == "AVAILABLE"
    assert "id" in data
    assert "created_at" in data


def test_create_vehicle_as_manager(client, manager_headers):
    payload = {
        "registration_number": "VAN-IL-402",
        "vehicle_type": "Electric Cargo Van",
        "capacity": 3500.00,
    }
    response = client.post("/api/v1/vehicles", json=payload, headers=manager_headers)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["registration_number"] == "VAN-IL-402"
    assert response.json()["status"] == "AVAILABLE"


def test_create_vehicle_rejected_for_driver(client, driver_headers):
    response = client.post("/api/v1/vehicles", json=SAMPLE_VEHICLE, headers=driver_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "Access forbidden" in response.json()["detail"]


def test_create_vehicle_rejected_for_viewer(client, viewer_headers):
    response = client.post("/api/v1/vehicles", json=SAMPLE_VEHICLE, headers=viewer_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_create_vehicle_unauthenticated(client):
    response = client.post("/api/v1/vehicles", json=SAMPLE_VEHICLE)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_vehicle_duplicate_registration_number(client, admin_headers):
    # First vehicle
    res1 = client.post("/api/v1/vehicles", json=SAMPLE_VEHICLE, headers=admin_headers)
    assert res1.status_code == status.HTTP_201_CREATED

    # Duplicate registration (case variation)
    dup_payload = {
        **SAMPLE_VEHICLE,
        "registration_number": "trk-tx-9001",
    }
    res2 = client.post("/api/v1/vehicles", json=dup_payload, headers=admin_headers)
    assert res2.status_code == status.HTTP_400_BAD_REQUEST
    assert "already exists" in res2.json()["detail"]


def test_create_vehicle_invalid_capacity(client, admin_headers):
    payload = {
        **SAMPLE_VEHICLE,
        "capacity": -100.00,
    }
    res = client.post("/api/v1/vehicles", json=payload, headers=admin_headers)
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ------------------------------------------------------------------------------
# 2. Get Vehicles Tests (All & By ID)
# ------------------------------------------------------------------------------
def test_get_all_vehicles_and_filters(client, admin_headers, viewer_headers):
    client.post(
        "/api/v1/vehicles",
        json={"registration_number": "TRK-01", "vehicle_type": "Van", "capacity": 3000, "status": "AVAILABLE"},
        headers=admin_headers,
    )
    client.post(
        "/api/v1/vehicles",
        json={"registration_number": "TRK-02", "vehicle_type": "Truck", "capacity": 8000, "status": "MAINTENANCE"},
        headers=admin_headers,
    )
    client.post(
        "/api/v1/vehicles",
        json={"registration_number": "TRK-03", "vehicle_type": "Semi", "capacity": 20000, "status": "DECOMMISSIONED"},
        headers=admin_headers,
    )

    # All authenticated can read
    all_res = client.get("/api/v1/vehicles", headers=viewer_headers)
    assert all_res.status_code == status.HTTP_200_OK
    assert len(all_res.json()) == 3

    # Filter status=MAINTENANCE
    maint_res = client.get("/api/v1/vehicles?status=MAINTENANCE", headers=viewer_headers)
    assert maint_res.status_code == status.HTTP_200_OK
    assert len(maint_res.json()) == 1
    assert maint_res.json()[0]["registration_number"] == "TRK-02"

    # Filter is_active=true (non-decommissioned)
    active_res = client.get("/api/v1/vehicles?is_active=true", headers=viewer_headers)
    assert active_res.status_code == status.HTTP_200_OK
    assert len(active_res.json()) == 2

    # Pagination
    page_res = client.get("/api/v1/vehicles?limit=1", headers=viewer_headers)
    assert page_res.status_code == status.HTTP_200_OK
    assert len(page_res.json()) == 1


def test_get_vehicle_by_id(client, admin_headers, driver_headers):
    create_res = client.post("/api/v1/vehicles", json=SAMPLE_VEHICLE, headers=admin_headers)
    veh_id = create_res.json()["id"]

    res = client.get(f"/api/v1/vehicles/{veh_id}", headers=driver_headers)
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["id"] == veh_id
    assert res.json()["registration_number"] == "TRK-TX-9001"


def test_get_vehicle_not_found(client, viewer_headers):
    res = client.get("/api/v1/vehicles/99999", headers=viewer_headers)
    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in res.json()["detail"].lower()


# ------------------------------------------------------------------------------
# 3. Update Vehicle Tests
# ------------------------------------------------------------------------------
def test_update_vehicle_as_admin(client, admin_headers):
    create_res = client.post("/api/v1/vehicles", json=SAMPLE_VEHICLE, headers=admin_headers)
    veh_id = create_res.json()["id"]

    update_payload = {"vehicle_type": "Modified Semi-Trailer", "capacity": 25000.00}
    put_res = client.put(f"/api/v1/vehicles/{veh_id}", json=update_payload, headers=admin_headers)
    assert put_res.status_code == status.HTTP_200_OK
    data = put_res.json()
    assert data["vehicle_type"] == "Modified Semi-Trailer"
    assert Decimal(str(data["capacity"])) == Decimal("25000.00")


def test_update_vehicle_as_manager(client, admin_headers, manager_headers):
    create_res = client.post("/api/v1/vehicles", json=SAMPLE_VEHICLE, headers=admin_headers)
    veh_id = create_res.json()["id"]

    patch_res = client.patch(
        f"/api/v1/vehicles/{veh_id}",
        json={"status": "IN_USE"},
        headers=manager_headers,
    )
    assert patch_res.status_code == status.HTTP_200_OK
    assert patch_res.json()["status"] == "IN_USE"


def test_update_vehicle_duplicate_registration_conflict(client, admin_headers):
    client.post("/api/v1/vehicles", json={**SAMPLE_VEHICLE, "registration_number": "REG-AAA"}, headers=admin_headers)
    v2 = client.post("/api/v1/vehicles", json={**SAMPLE_VEHICLE, "registration_number": "REG-BBB"}, headers=admin_headers).json()

    res = client.patch(f"/api/v1/vehicles/{v2['id']}", json={"registration_number": "reg-aaa"}, headers=admin_headers)
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert "already exists" in res.json()["detail"]


def test_update_vehicle_rejected_for_driver_and_viewer(client, admin_headers, driver_headers, viewer_headers):
    v = client.post("/api/v1/vehicles", json=SAMPLE_VEHICLE, headers=admin_headers).json()

    assert client.put(f"/api/v1/vehicles/{v['id']}", json={"status": "HACK"}, headers=driver_headers).status_code == status.HTTP_403_FORBIDDEN
    assert client.put(f"/api/v1/vehicles/{v['id']}", json={"status": "HACK"}, headers=viewer_headers).status_code == status.HTTP_403_FORBIDDEN


def test_update_vehicle_not_found(client, admin_headers):
    res = client.put("/api/v1/vehicles/99999", json={"status": "IN_USE"}, headers=admin_headers)
    assert res.status_code == status.HTTP_404_NOT_FOUND


def test_update_vehicle_invalid_capacity(client, admin_headers):
    v = client.post("/api/v1/vehicles", json=SAMPLE_VEHICLE, headers=admin_headers).json()
    res = client.patch(f"/api/v1/vehicles/{v['id']}", json={"capacity": -50}, headers=admin_headers)
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ------------------------------------------------------------------------------
# 4. Delete Vehicle Tests
# ------------------------------------------------------------------------------
def test_delete_vehicle_as_admin(client, admin_headers, viewer_headers):
    v = client.post("/api/v1/vehicles", json=SAMPLE_VEHICLE, headers=admin_headers).json()
    veh_id = v["id"]

    del_res = client.delete(f"/api/v1/vehicles/{veh_id}", headers=admin_headers)
    assert del_res.status_code == status.HTTP_200_OK
    assert "deleted successfully" in del_res.json()["message"]

    # Subsequent GET returns 404
    get_res = client.get(f"/api/v1/vehicles/{veh_id}", headers=viewer_headers)
    assert get_res.status_code == status.HTTP_404_NOT_FOUND


def test_delete_vehicle_rejected_for_manager(client, admin_headers, manager_headers):
    v = client.post("/api/v1/vehicles", json=SAMPLE_VEHICLE, headers=admin_headers).json()
    del_res = client.delete(f"/api/v1/vehicles/{v['id']}", headers=manager_headers)
    assert del_res.status_code == status.HTTP_403_FORBIDDEN


def test_delete_vehicle_rejected_for_driver_and_viewer(client, admin_headers, driver_headers, viewer_headers):
    v = client.post("/api/v1/vehicles", json=SAMPLE_VEHICLE, headers=admin_headers).json()
    assert client.delete(f"/api/v1/vehicles/{v['id']}", headers=driver_headers).status_code == status.HTTP_403_FORBIDDEN
    assert client.delete(f"/api/v1/vehicles/{v['id']}", headers=viewer_headers).status_code == status.HTTP_403_FORBIDDEN


def test_delete_vehicle_not_found(client, admin_headers):
    res = client.delete("/api/v1/vehicles/99999", headers=admin_headers)
    assert res.status_code == status.HTTP_404_NOT_FOUND
