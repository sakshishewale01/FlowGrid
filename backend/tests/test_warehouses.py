"""
FlowGrid - Warehouse Management Backend Tests
============================================
Comprehensive test suite validating:
- Warehouse CRUD operations with layered architecture (Repository, Service, Endpoint).
- Role-Based Access Control (RBAC):
  * Create: ADMIN, MANAGER allowed; DRIVER, VIEWER forbidden (403).
  * Read (all & by ID): All authenticated roles allowed.
  * Update (PUT & PATCH): ADMIN, MANAGER allowed; DRIVER, VIEWER forbidden (403).
  * Delete (soft-delete): ADMIN only; MANAGER, DRIVER, VIEWER forbidden (403).
- Input validation (capacity > 0, field lengths).
- 404 Not Found handling for non-existent warehouse entities.
- Pagination and active-status filtering.
"""

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
    """
    Creates clean schema before each test and resets dependency overrides.
    """
    Base.metadata.create_all(bind=test_engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client():
    return TestClient(app)


def get_auth_headers_for_role(client: TestClient, email: str, role: str) -> dict:
    """
    Helper to register a user with a given role, log in, and return Authorization headers.
    """
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
    return get_auth_headers_for_role(client, "admin@flowgrid.io", "ADMIN")


@pytest.fixture
def manager_headers(client):
    return get_auth_headers_for_role(client, "manager@flowgrid.io", "MANAGER")


@pytest.fixture
def driver_headers(client):
    return get_auth_headers_for_role(client, "driver@flowgrid.io", "DRIVER")


@pytest.fixture
def viewer_headers(client):
    return get_auth_headers_for_role(client, "viewer@flowgrid.io", "VIEWER")


SAMPLE_WAREHOUSE_PAYLOAD = {
    "name": "Chicago Central Distribution Hub",
    "location": "Chicago, IL",
    "address": "1200 Logistics Blvd, Dock 4, Chicago, IL 60601",
    "capacity": 75000,
    "is_active": True,
}


# ------------------------------------------------------------------------------
# 1. Create Warehouse Tests
# ------------------------------------------------------------------------------
def test_create_warehouse_as_admin(client, admin_headers):
    response = client.post(
        "/api/v1/warehouses",
        json=SAMPLE_WAREHOUSE_PAYLOAD,
        headers=admin_headers,
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == SAMPLE_WAREHOUSE_PAYLOAD["name"]
    assert data["location"] == SAMPLE_WAREHOUSE_PAYLOAD["location"]
    assert data["address"] == SAMPLE_WAREHOUSE_PAYLOAD["address"]
    assert data["capacity"] == 75000
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_warehouse_as_manager(client, manager_headers):
    payload = {
        "name": "Dallas Regional Terminal",
        "location": "Dallas, TX",
        "address": "450 Freight Way, Dallas, TX 75201",
        "capacity": 50000,
        "is_active": True,
    }
    response = client.post(
        "/api/v1/warehouses",
        json=payload,
        headers=manager_headers,
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["name"] == "Dallas Regional Terminal"


def test_create_warehouse_rejected_for_driver(client, driver_headers):
    response = client.post(
        "/api/v1/warehouses",
        json=SAMPLE_WAREHOUSE_PAYLOAD,
        headers=driver_headers,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "Access forbidden" in response.json()["detail"]


def test_create_warehouse_rejected_for_viewer(client, viewer_headers):
    response = client.post(
        "/api/v1/warehouses",
        json=SAMPLE_WAREHOUSE_PAYLOAD,
        headers=viewer_headers,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "Access forbidden" in response.json()["detail"]


def test_create_warehouse_unauthenticated(client):
    response = client.post("/api/v1/warehouses", json=SAMPLE_WAREHOUSE_PAYLOAD)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_warehouse_validation_errors(client, admin_headers):
    # Invalid capacity <= 0
    invalid_capacity_payload = {
        **SAMPLE_WAREHOUSE_PAYLOAD,
        "capacity": 0,
    }
    res1 = client.post(
        "/api/v1/warehouses",
        json=invalid_capacity_payload,
        headers=admin_headers,
    )
    assert res1.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Missing address
    missing_address = {
        "name": "Test Warehouse",
        "location": "Miami, FL",
        "capacity": 1000,
    }
    res2 = client.post(
        "/api/v1/warehouses",
        json=missing_address,
        headers=admin_headers,
    )
    assert res2.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ------------------------------------------------------------------------------
# 2. Get Warehouses Tests (All & By ID)
# ------------------------------------------------------------------------------
def test_get_all_warehouses(client, admin_headers, viewer_headers):
    # Create two warehouses as Admin
    client.post(
        "/api/v1/warehouses",
        json={
            "name": "Atlanta Hub",
            "location": "Atlanta, GA",
            "address": "10 Peachtree St, Atlanta, GA 30303",
            "capacity": 30000,
        },
        headers=admin_headers,
    )
    client.post(
        "/api/v1/warehouses",
        json={
            "name": "Seattle Hub",
            "location": "Seattle, WA",
            "address": "200 Pike St, Seattle, WA 98101",
            "capacity": 40000,
        },
        headers=admin_headers,
    )

    # All authenticated users (including Viewer) can read warehouses
    res = client.get("/api/v1/warehouses", headers=viewer_headers)
    assert res.status_code == status.HTTP_200_OK
    items = res.json()
    assert len(items) == 2
    assert items[0]["name"] == "Atlanta Hub"
    assert items[1]["name"] == "Seattle Hub"


def test_get_warehouses_pagination_and_filter(client, admin_headers, viewer_headers):
    # Create active and inactive warehouses
    client.post(
        "/api/v1/warehouses",
        json={**SAMPLE_WAREHOUSE_PAYLOAD, "name": "Active Hub 1", "is_active": True},
        headers=admin_headers,
    )
    client.post(
        "/api/v1/warehouses",
        json={**SAMPLE_WAREHOUSE_PAYLOAD, "name": "Inactive Hub", "is_active": False},
        headers=admin_headers,
    )

    # Test is_active=true filter
    active_res = client.get(
        "/api/v1/warehouses?is_active=true",
        headers=viewer_headers,
    )
    assert active_res.status_code == status.HTTP_200_OK
    assert len(active_res.json()) == 1
    assert active_res.json()[0]["name"] == "Active Hub 1"

    # Test pagination: limit=1
    limit_res = client.get(
        "/api/v1/warehouses?limit=1",
        headers=viewer_headers,
    )
    assert limit_res.status_code == status.HTTP_200_OK
    assert len(limit_res.json()) == 1


def test_get_warehouse_by_id(client, admin_headers, driver_headers):
    create_res = client.post(
        "/api/v1/warehouses",
        json=SAMPLE_WAREHOUSE_PAYLOAD,
        headers=admin_headers,
    )
    warehouse_id = create_res.json()["id"]

    # Driver can retrieve warehouse by ID
    get_res = client.get(f"/api/v1/warehouses/{warehouse_id}", headers=driver_headers)
    assert get_res.status_code == status.HTTP_200_OK
    assert get_res.json()["id"] == warehouse_id
    assert get_res.json()["name"] == SAMPLE_WAREHOUSE_PAYLOAD["name"]


def test_get_warehouse_not_found(client, viewer_headers):
    response = client.get("/api/v1/warehouses/99999", headers=viewer_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"].lower()


# ------------------------------------------------------------------------------
# 3. Update Warehouse Tests
# ------------------------------------------------------------------------------
def test_update_warehouse_as_admin(client, admin_headers):
    create_res = client.post(
        "/api/v1/warehouses",
        json=SAMPLE_WAREHOUSE_PAYLOAD,
        headers=admin_headers,
    )
    warehouse_id = create_res.json()["id"]

    update_payload = {
        "name": "Chicago Super Hub (Renovated)",
        "capacity": 120000,
    }
    update_res = client.put(
        f"/api/v1/warehouses/{warehouse_id}",
        json=update_payload,
        headers=admin_headers,
    )
    assert update_res.status_code == status.HTTP_200_OK
    updated_data = update_res.json()
    assert updated_data["name"] == "Chicago Super Hub (Renovated)"
    assert updated_data["capacity"] == 120000
    # Location and address should remain unchanged
    assert updated_data["location"] == SAMPLE_WAREHOUSE_PAYLOAD["location"]


def test_update_warehouse_as_manager(client, admin_headers, manager_headers):
    create_res = client.post(
        "/api/v1/warehouses",
        json=SAMPLE_WAREHOUSE_PAYLOAD,
        headers=admin_headers,
    )
    warehouse_id = create_res.json()["id"]

    update_payload = {"location": "Greater Chicago Metropolitan Area"}
    patch_res = client.patch(
        f"/api/v1/warehouses/{warehouse_id}",
        json=update_payload,
        headers=manager_headers,
    )
    assert patch_res.status_code == status.HTTP_200_OK
    assert patch_res.json()["location"] == "Greater Chicago Metropolitan Area"


def test_update_warehouse_rejected_for_driver_and_viewer(
    client, admin_headers, driver_headers, viewer_headers
):
    create_res = client.post(
        "/api/v1/warehouses",
        json=SAMPLE_WAREHOUSE_PAYLOAD,
        headers=admin_headers,
    )
    warehouse_id = create_res.json()["id"]

    # Driver attempt
    d_res = client.put(
        f"/api/v1/warehouses/{warehouse_id}",
        json={"name": "Hacked by Driver"},
        headers=driver_headers,
    )
    assert d_res.status_code == status.HTTP_403_FORBIDDEN

    # Viewer attempt
    v_res = client.put(
        f"/api/v1/warehouses/{warehouse_id}",
        json={"name": "Hacked by Viewer"},
        headers=viewer_headers,
    )
    assert v_res.status_code == status.HTTP_403_FORBIDDEN


def test_update_warehouse_not_found(client, admin_headers):
    res = client.put(
        "/api/v1/warehouses/99999",
        json={"name": "Does not exist"},
        headers=admin_headers,
    )
    assert res.status_code == status.HTTP_404_NOT_FOUND


def test_update_warehouse_invalid_capacity(client, admin_headers):
    create_res = client.post(
        "/api/v1/warehouses",
        json=SAMPLE_WAREHOUSE_PAYLOAD,
        headers=admin_headers,
    )
    warehouse_id = create_res.json()["id"]

    res = client.put(
        f"/api/v1/warehouses/{warehouse_id}",
        json={"capacity": -100},
        headers=admin_headers,
    )
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ------------------------------------------------------------------------------
# 4. Delete Warehouse Tests (Soft Delete)
# ------------------------------------------------------------------------------
def test_delete_warehouse_as_admin_soft_deletes(client, admin_headers, viewer_headers):
    create_res = client.post(
        "/api/v1/warehouses",
        json=SAMPLE_WAREHOUSE_PAYLOAD,
        headers=admin_headers,
    )
    warehouse_id = create_res.json()["id"]

    delete_res = client.delete(
        f"/api/v1/warehouses/{warehouse_id}",
        headers=admin_headers,
    )
    assert delete_res.status_code == status.HTTP_200_OK
    assert delete_res.json()["is_active"] is False

    # Confirm soft-deleted state persists on subsequent get
    fetch_res = client.get(
        f"/api/v1/warehouses/{warehouse_id}",
        headers=viewer_headers,
    )
    assert fetch_res.status_code == status.HTTP_200_OK
    assert fetch_res.json()["is_active"] is False


def test_delete_warehouse_rejected_for_manager(client, admin_headers, manager_headers):
    create_res = client.post(
        "/api/v1/warehouses",
        json=SAMPLE_WAREHOUSE_PAYLOAD,
        headers=admin_headers,
    )
    warehouse_id = create_res.json()["id"]

    # Manager cannot delete
    del_res = client.delete(
        f"/api/v1/warehouses/{warehouse_id}",
        headers=manager_headers,
    )
    assert del_res.status_code == status.HTTP_403_FORBIDDEN


def test_delete_warehouse_rejected_for_driver_and_viewer(
    client, admin_headers, driver_headers, viewer_headers
):
    create_res = client.post(
        "/api/v1/warehouses",
        json=SAMPLE_WAREHOUSE_PAYLOAD,
        headers=admin_headers,
    )
    warehouse_id = create_res.json()["id"]

    assert (
        client.delete(
            f"/api/v1/warehouses/{warehouse_id}", headers=driver_headers
        ).status_code
        == status.HTTP_403_FORBIDDEN
    )
    assert (
        client.delete(
            f"/api/v1/warehouses/{warehouse_id}", headers=viewer_headers
        ).status_code
        == status.HTTP_403_FORBIDDEN
    )


def test_delete_warehouse_not_found(client, admin_headers):
    res = client.delete("/api/v1/warehouses/99999", headers=admin_headers)
    assert res.status_code == status.HTTP_404_NOT_FOUND
