"""
FlowGrid - Driver Management Backend Tests
=========================================
Comprehensive test suite validating:
- Driver CRUD operations with layered architecture (Repository, Service, Endpoint).
- Linkage to User accounts and verification of user existence/active status.
- License uniqueness validation (case-insensitive) and duplicate user profile prevention.
- Role-Based Access Control (RBAC):
  * Create: ADMIN, MANAGER allowed; DRIVER, VIEWER forbidden (403).
  * Read: All authenticated roles allowed.
  * Update (PUT & PATCH): ADMIN, MANAGER allowed; DRIVER, VIEWER forbidden (403).
  * Delete: ADMIN only; MANAGER, DRIVER, VIEWER forbidden (403).
- Input validation (license length, phone length).
- 404 Not Found handling for non-existent driver entities.
- Filtering by availability status and pagination.
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
    return get_auth_headers_for_role(client, "admin_drv@flowgrid.io", "ADMIN")


@pytest.fixture
def manager_headers(client):
    return get_auth_headers_for_role(client, "manager_drv@flowgrid.io", "MANAGER")


@pytest.fixture
def driver_headers(client):
    return get_auth_headers_for_role(client, "driver_drv@flowgrid.io", "DRIVER")


@pytest.fixture
def viewer_headers(client):
    return get_auth_headers_for_role(client, "viewer_drv@flowgrid.io", "VIEWER")


def create_sample_user(client: TestClient, email: str, name: str = "Driver User", is_active: bool = True) -> int:
    reg_res = client.post(
        "/api/v1/auth/register",
        json={
            "name": name,
            "email": email,
            "password": "DriverPassword123!",
            "role": "DRIVER",
        },
    )
    return reg_res.json()["id"]


# ------------------------------------------------------------------------------
# 1. Create Driver Tests
# ------------------------------------------------------------------------------
def test_create_driver_as_admin(client, admin_headers):
    user_id = create_sample_user(client, "d1@flowgrid.io", "Dave Driver")
    payload = {
        "user_id": user_id,
        "license_number": "CDL-9482-TX",
        "phone_number": "+1-555-019-2834",
        "availability_status": "AVAILABLE",
    }
    response = client.post("/api/v1/drivers", json=payload, headers=admin_headers)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["user_id"] == user_id
    assert data["license_number"] == "CDL-9482-TX"
    assert data["phone_number"] == "+1-555-019-2834"
    assert data["availability_status"] == "AVAILABLE"
    assert "id" in data
    assert "created_at" in data
    assert data["user"]["email"] == "d1@flowgrid.io"


def test_create_driver_as_manager(client, manager_headers):
    user_id = create_sample_user(client, "d2@flowgrid.io", "Dan Driver")
    payload = {
        "user_id": user_id,
        "license_number": "CDL-1102-IL",
        "phone_number": "+1-555-302-9988",
    }
    response = client.post("/api/v1/drivers", json=payload, headers=manager_headers)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["license_number"] == "CDL-1102-IL"
    assert response.json()["availability_status"] == "AVAILABLE"


def test_create_driver_rejected_for_driver(client, driver_headers):
    user_id = create_sample_user(client, "d3@flowgrid.io", "Denise Driver")
    payload = {
        "user_id": user_id,
        "license_number": "CDL-3333-CA",
        "phone_number": "+1-555-404-5555",
    }
    response = client.post("/api/v1/drivers", json=payload, headers=driver_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "Access forbidden" in response.json()["detail"]


def test_create_driver_rejected_for_viewer(client, viewer_headers):
    user_id = create_sample_user(client, "d4@flowgrid.io", "Doug Driver")
    payload = {
        "user_id": user_id,
        "license_number": "CDL-4444-NY",
        "phone_number": "+1-555-404-6666",
    }
    response = client.post("/api/v1/drivers", json=payload, headers=viewer_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_create_driver_unauthenticated(client):
    payload = {
        "user_id": 1,
        "license_number": "CDL-5555-FL",
        "phone_number": "+1-555-404-7777",
    }
    response = client.post("/api/v1/drivers", json=payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_driver_duplicate_user_id(client, admin_headers):
    user_id = create_sample_user(client, "dup_user@flowgrid.io", "Dup User")
    payload = {
        "user_id": user_id,
        "license_number": "CDL-DUP-01",
        "phone_number": "+1-555-111-2222",
    }
    # First profile
    res1 = client.post("/api/v1/drivers", json=payload, headers=admin_headers)
    assert res1.status_code == status.HTTP_201_CREATED

    # Attempt second profile for same user
    payload2 = {
        "user_id": user_id,
        "license_number": "CDL-DUP-02",
        "phone_number": "+1-555-111-3333",
    }
    res2 = client.post("/api/v1/drivers", json=payload2, headers=admin_headers)
    assert res2.status_code == status.HTTP_400_BAD_REQUEST
    assert "already linked" in res2.json()["detail"]


def test_create_driver_duplicate_license_number(client, admin_headers):
    u1 = create_sample_user(client, "lic1@flowgrid.io", "Driver Lic 1")
    u2 = create_sample_user(client, "lic2@flowgrid.io", "Driver Lic 2")

    res1 = client.post(
        "/api/v1/drivers",
        json={"user_id": u1, "license_number": "CDL-UNIQUE-99", "phone_number": "+1-555-123-4567"},
        headers=admin_headers,
    )
    assert res1.status_code == status.HTTP_201_CREATED

    # Duplicate license with lower-case test
    res2 = client.post(
        "/api/v1/drivers",
        json={"user_id": u2, "license_number": "cdl-unique-99", "phone_number": "+1-555-987-6543"},
        headers=admin_headers,
    )
    assert res2.status_code == status.HTTP_400_BAD_REQUEST
    assert "already exists" in res2.json()["detail"]


def test_create_driver_invalid_user_id(client, admin_headers):
    payload = {
        "user_id": 99999,
        "license_number": "CDL-GHOST-1",
        "phone_number": "+1-555-000-0000",
    }
    response = client.post("/api/v1/drivers", json=payload, headers=admin_headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "does not exist" in response.json()["detail"]


def test_create_driver_validation_errors(client, admin_headers):
    # License too short (<3)
    res1 = client.post(
        "/api/v1/drivers",
        json={"user_id": 1, "license_number": "AB", "phone_number": "+1-555-123-4567"},
        headers=admin_headers,
    )
    assert res1.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Phone number too short (<7)
    res2 = client.post(
        "/api/v1/drivers",
        json={"user_id": 1, "license_number": "CDL-123", "phone_number": "123"},
        headers=admin_headers,
    )
    assert res2.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ------------------------------------------------------------------------------
# 2. Get Drivers Tests (All & By ID)
# ------------------------------------------------------------------------------
def test_get_all_drivers_and_filters(client, admin_headers, viewer_headers):
    u1 = create_sample_user(client, "list1@flowgrid.io", "List Driver 1")
    u2 = create_sample_user(client, "list2@flowgrid.io", "List Driver 2")

    client.post(
        "/api/v1/drivers",
        json={"user_id": u1, "license_number": "CDL-LST-01", "phone_number": "+1-555-111-0001", "availability_status": "AVAILABLE"},
        headers=admin_headers,
    )
    client.post(
        "/api/v1/drivers",
        json={"user_id": u2, "license_number": "CDL-LST-02", "phone_number": "+1-555-111-0002", "availability_status": "ON_DUTY"},
        headers=admin_headers,
    )

    # All authenticated roles can list
    all_res = client.get("/api/v1/drivers", headers=viewer_headers)
    assert all_res.status_code == status.HTTP_200_OK
    assert len(all_res.json()) == 2

    # Filter by availability_status=ON_DUTY
    duty_res = client.get("/api/v1/drivers?availability_status=ON_DUTY", headers=viewer_headers)
    assert duty_res.status_code == status.HTTP_200_OK
    assert len(duty_res.json()) == 1
    assert duty_res.json()[0]["availability_status"] == "ON_DUTY"

    # Pagination
    limit_res = client.get("/api/v1/drivers?limit=1", headers=viewer_headers)
    assert limit_res.status_code == status.HTTP_200_OK
    assert len(limit_res.json()) == 1


def test_get_driver_by_id(client, admin_headers, driver_headers):
    user_id = create_sample_user(client, "get_by_id@flowgrid.io", "Get Driver")
    create_res = client.post(
        "/api/v1/drivers",
        json={"user_id": user_id, "license_number": "CDL-GET-ID", "phone_number": "+1-555-900-1234"},
        headers=admin_headers,
    )
    driver_id = create_res.json()["id"]

    res = client.get(f"/api/v1/drivers/{driver_id}", headers=driver_headers)
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["id"] == driver_id
    assert res.json()["license_number"] == "CDL-GET-ID"


def test_get_driver_not_found(client, viewer_headers):
    res = client.get("/api/v1/drivers/99999", headers=viewer_headers)
    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in res.json()["detail"].lower()


# ------------------------------------------------------------------------------
# 3. Update Driver Tests
# ------------------------------------------------------------------------------
def test_update_driver_as_admin(client, admin_headers):
    u = create_sample_user(client, "upd_adm@flowgrid.io", "Upd Admin Driver")
    create_res = client.post(
        "/api/v1/drivers",
        json={"user_id": u, "license_number": "CDL-UPD-01", "phone_number": "+1-555-222-3333"},
        headers=admin_headers,
    )
    driver_id = create_res.json()["id"]

    update_payload = {"phone_number": "+1-555-999-8888", "availability_status": "IN_TRANSIT"}
    put_res = client.put(f"/api/v1/drivers/{driver_id}", json=update_payload, headers=admin_headers)
    assert put_res.status_code == status.HTTP_200_OK
    data = put_res.json()
    assert data["phone_number"] == "+1-555-999-8888"
    assert data["availability_status"] == "IN_TRANSIT"


def test_update_driver_as_manager(client, admin_headers, manager_headers):
    u = create_sample_user(client, "upd_mgr@flowgrid.io", "Upd Mgr Driver")
    create_res = client.post(
        "/api/v1/drivers",
        json={"user_id": u, "license_number": "CDL-MGR-UPD", "phone_number": "+1-555-444-5555"},
        headers=admin_headers,
    )
    driver_id = create_res.json()["id"]

    patch_res = client.patch(
        f"/api/v1/drivers/{driver_id}",
        json={"availability_status": "OFF_DUTY"},
        headers=manager_headers,
    )
    assert patch_res.status_code == status.HTTP_200_OK
    assert patch_res.json()["availability_status"] == "OFF_DUTY"


def test_update_driver_duplicate_license_conflict(client, admin_headers):
    u1 = create_sample_user(client, "c1@flowgrid.io", "Conflict Driver 1")
    u2 = create_sample_user(client, "c2@flowgrid.io", "Conflict Driver 2")

    client.post("/api/v1/drivers", json={"user_id": u1, "license_number": "CDL-FIRST-01", "phone_number": "+1-555-111-1111"}, headers=admin_headers)
    d2 = client.post("/api/v1/drivers", json={"user_id": u2, "license_number": "CDL-SECOND-02", "phone_number": "+1-555-222-2222"}, headers=admin_headers).json()

    # Attempt to change d2's license to d1's license
    res = client.patch(f"/api/v1/drivers/{d2['id']}", json={"license_number": "cdl-first-01"}, headers=admin_headers)
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert "already exists" in res.json()["detail"]


def test_update_driver_rejected_for_driver_and_viewer(client, admin_headers, driver_headers, viewer_headers):
    u = create_sample_user(client, "rej_upd@flowgrid.io", "Reject Upd")
    d = client.post("/api/v1/drivers", json={"user_id": u, "license_number": "CDL-REJ-01", "phone_number": "+1-555-333-3333"}, headers=admin_headers).json()

    assert client.put(f"/api/v1/drivers/{d['id']}", json={"phone_number": "+1-555-000-1111"}, headers=driver_headers).status_code == status.HTTP_403_FORBIDDEN
    assert client.put(f"/api/v1/drivers/{d['id']}", json={"phone_number": "+1-555-000-1111"}, headers=viewer_headers).status_code == status.HTTP_403_FORBIDDEN


def test_update_driver_not_found(client, admin_headers):
    res = client.put("/api/v1/drivers/99999", json={"phone_number": "+1-555-000-9999"}, headers=admin_headers)
    assert res.status_code == status.HTTP_404_NOT_FOUND


# ------------------------------------------------------------------------------
# 4. Delete Driver Tests
# ------------------------------------------------------------------------------
def test_delete_driver_as_admin(client, admin_headers, viewer_headers):
    u = create_sample_user(client, "del_adm@flowgrid.io", "Del Admin Driver")
    d = client.post("/api/v1/drivers", json={"user_id": u, "license_number": "CDL-DEL-01", "phone_number": "+1-555-777-8888"}, headers=admin_headers).json()
    driver_id = d["id"]

    del_res = client.delete(f"/api/v1/drivers/{driver_id}", headers=admin_headers)
    assert del_res.status_code == status.HTTP_200_OK
    assert "deleted successfully" in del_res.json()["message"]

    # Subsequent GET returns 404
    get_res = client.get(f"/api/v1/drivers/{driver_id}", headers=viewer_headers)
    assert get_res.status_code == status.HTTP_404_NOT_FOUND


def test_delete_driver_rejected_for_manager(client, admin_headers, manager_headers):
    u = create_sample_user(client, "del_mgr@flowgrid.io", "Del Mgr Driver")
    d = client.post("/api/v1/drivers", json={"user_id": u, "license_number": "CDL-MGR-DEL", "phone_number": "+1-555-888-9999"}, headers=admin_headers).json()

    del_res = client.delete(f"/api/v1/drivers/{d['id']}", headers=manager_headers)
    assert del_res.status_code == status.HTTP_403_FORBIDDEN


def test_delete_driver_rejected_for_driver_and_viewer(client, admin_headers, driver_headers, viewer_headers):
    u = create_sample_user(client, "del_view@flowgrid.io", "Del View Driver")
    d = client.post("/api/v1/drivers", json={"user_id": u, "license_number": "CDL-VIEW-DEL", "phone_number": "+1-555-999-0000"}, headers=admin_headers).json()

    assert client.delete(f"/api/v1/drivers/{d['id']}", headers=driver_headers).status_code == status.HTTP_403_FORBIDDEN
    assert client.delete(f"/api/v1/drivers/{d['id']}", headers=viewer_headers).status_code == status.HTTP_403_FORBIDDEN


def test_delete_driver_not_found(client, admin_headers):
    res = client.delete("/api/v1/drivers/99999", headers=admin_headers)
    assert res.status_code == status.HTTP_404_NOT_FOUND
