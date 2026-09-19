"""
FlowGrid - Inventory Management Backend Tests
============================================
Comprehensive test suite validating:
- Inventory CRUD operations with layered architecture (Repository, Service, Endpoint).
- Relational validation:
  * Warehouse existence and active check.
  * Product existence and active check.
  * Unique constraint on (warehouse_id, product_id) preventing duplicates.
- Role-Based Access Control (RBAC):
  * Create: ADMIN, MANAGER allowed; DRIVER, VIEWER forbidden (403).
  * Read (all & by ID): All authenticated roles allowed.
  * Update (PUT & PATCH): ADMIN, MANAGER allowed; DRIVER, VIEWER forbidden (403).
  * Delete: ADMIN only; MANAGER, DRIVER, VIEWER forbidden (403).
- Input validation (quantity >= 0, reorder_level >= 0).
- 404 Not Found handling for non-existent inventory entities.
- Filtering by warehouse_id, product_id, and pagination.
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
    return get_auth_headers_for_role(client, "admin_inv@flowgrid.io", "ADMIN")


@pytest.fixture
def manager_headers(client):
    return get_auth_headers_for_role(client, "manager_inv@flowgrid.io", "MANAGER")


@pytest.fixture
def driver_headers(client):
    return get_auth_headers_for_role(client, "driver_inv@flowgrid.io", "DRIVER")


@pytest.fixture
def viewer_headers(client):
    return get_auth_headers_for_role(client, "viewer_inv@flowgrid.io", "VIEWER")


@pytest.fixture
def active_warehouse(client, admin_headers):
    res = client.post(
        "/api/v1/warehouses",
        json={
            "name": "Dallas Logistics Hub",
            "location": "Dallas, TX",
            "address": "500 Logistics Blvd, Dallas, TX 75201",
            "capacity": 60000,
            "is_active": True,
        },
        headers=admin_headers,
    )
    return res.json()


@pytest.fixture
def active_product(client, admin_headers):
    res = client.post(
        "/api/v1/products",
        json={
            "name": "Industrial Pallet Wrap 500m",
            "sku": "WRAP-IND-500",
            "description": "Commercial cling pallet wrap.",
            "unit_price": 28.50,
            "is_active": True,
        },
        headers=admin_headers,
    )
    return res.json()


# ------------------------------------------------------------------------------
# 1. Create Inventory Tests
# ------------------------------------------------------------------------------
def test_create_inventory_as_admin(client, admin_headers, active_warehouse, active_product):
    payload = {
        "warehouse_id": active_warehouse["id"],
        "product_id": active_product["id"],
        "quantity": 150,
        "reorder_level": 25,
    }
    response = client.post(
        "/api/v1/inventory",
        json=payload,
        headers=admin_headers,
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["warehouse_id"] == active_warehouse["id"]
    assert data["product_id"] == active_product["id"]
    assert data["quantity"] == 150
    assert data["reorder_level"] == 25
    assert "id" in data
    assert "updated_at" in data
    assert data["warehouse"]["name"] == active_warehouse["name"]
    assert data["product"]["sku"] == active_product["sku"]


def test_create_inventory_as_manager(client, manager_headers, active_warehouse, active_product):
    payload = {
        "warehouse_id": active_warehouse["id"],
        "product_id": active_product["id"],
        "quantity": 80,
        "reorder_level": 15,
    }
    response = client.post(
        "/api/v1/inventory",
        json=payload,
        headers=manager_headers,
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["quantity"] == 80


def test_create_inventory_rejected_for_driver(client, driver_headers, active_warehouse, active_product):
    payload = {
        "warehouse_id": active_warehouse["id"],
        "product_id": active_product["id"],
        "quantity": 50,
    }
    response = client.post(
        "/api/v1/inventory",
        json=payload,
        headers=driver_headers,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "Access forbidden" in response.json()["detail"]


def test_create_inventory_rejected_for_viewer(client, viewer_headers, active_warehouse, active_product):
    payload = {
        "warehouse_id": active_warehouse["id"],
        "product_id": active_product["id"],
        "quantity": 50,
    }
    response = client.post(
        "/api/v1/inventory",
        json=payload,
        headers=viewer_headers,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "Access forbidden" in response.json()["detail"]


def test_create_inventory_unauthenticated(client, active_warehouse, active_product):
    payload = {
        "warehouse_id": active_warehouse["id"],
        "product_id": active_product["id"],
        "quantity": 10,
    }
    response = client.post("/api/v1/inventory", json=payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_inventory_duplicate_combination(client, admin_headers, active_warehouse, active_product):
    payload = {
        "warehouse_id": active_warehouse["id"],
        "product_id": active_product["id"],
        "quantity": 100,
        "reorder_level": 20,
    }
    # First creation succeeds
    res1 = client.post("/api/v1/inventory", json=payload, headers=admin_headers)
    assert res1.status_code == status.HTTP_201_CREATED

    # Duplicate creation fails safely with HTTP 400
    res2 = client.post("/api/v1/inventory", json=payload, headers=admin_headers)
    assert res2.status_code == status.HTTP_400_BAD_REQUEST
    assert "already exists" in res2.json()["detail"]


def test_create_inventory_invalid_warehouse_id(client, admin_headers, active_product):
    payload = {
        "warehouse_id": 99999,
        "product_id": active_product["id"],
        "quantity": 50,
    }
    response = client.post("/api/v1/inventory", json=payload, headers=admin_headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Warehouse with ID 99999 does not exist" in response.json()["detail"]


def test_create_inventory_invalid_product_id(client, admin_headers, active_warehouse):
    payload = {
        "warehouse_id": active_warehouse["id"],
        "product_id": 99999,
        "quantity": 50,
    }
    response = client.post("/api/v1/inventory", json=payload, headers=admin_headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Product with ID 99999 does not exist" in response.json()["detail"]


def test_create_inventory_inactive_warehouse(client, admin_headers, active_product):
    # Create and soft-delete a warehouse
    w_res = client.post(
        "/api/v1/warehouses",
        json={
            "name": "Inactive Hub",
            "location": "Nevada",
            "address": "Desert Way 1",
            "capacity": 10000,
            "is_active": False,
        },
        headers=admin_headers,
    )
    inactive_w_id = w_res.json()["id"]

    payload = {
        "warehouse_id": inactive_w_id,
        "product_id": active_product["id"],
        "quantity": 10,
    }
    res = client.post("/api/v1/inventory", json=payload, headers=admin_headers)
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert "is inactive" in res.json()["detail"]


def test_create_inventory_inactive_product(client, admin_headers, active_warehouse):
    # Create and soft-delete a product
    p_res = client.post(
        "/api/v1/products",
        json={
            "name": "Inactive Product",
            "sku": "INACT-SKU-99",
            "unit_price": 10.0,
            "is_active": False,
        },
        headers=admin_headers,
    )
    inactive_p_id = p_res.json()["id"]

    payload = {
        "warehouse_id": active_warehouse["id"],
        "product_id": inactive_p_id,
        "quantity": 10,
    }
    res = client.post("/api/v1/inventory", json=payload, headers=admin_headers)
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert "is inactive" in res.json()["detail"]


def test_create_inventory_negative_quantity_and_reorder_level(client, admin_headers, active_warehouse, active_product):
    # Negative quantity
    res1 = client.post(
        "/api/v1/inventory",
        json={
            "warehouse_id": active_warehouse["id"],
            "product_id": active_product["id"],
            "quantity": -5,
        },
        headers=admin_headers,
    )
    assert res1.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Negative reorder level
    res2 = client.post(
        "/api/v1/inventory",
        json={
            "warehouse_id": active_warehouse["id"],
            "product_id": active_product["id"],
            "reorder_level": -1,
        },
        headers=admin_headers,
    )
    assert res2.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ------------------------------------------------------------------------------
# 2. Get Inventory Tests (All, Filters, and By ID)
# ------------------------------------------------------------------------------
def test_get_all_inventory_and_filters(client, admin_headers, viewer_headers):
    # Create 2 warehouses
    w1 = client.post(
        "/api/v1/warehouses",
        json={"name": "Hub 1", "location": "Loc 1", "address": "Addr 1", "capacity": 1000},
        headers=admin_headers,
    ).json()
    w2 = client.post(
        "/api/v1/warehouses",
        json={"name": "Hub 2", "location": "Loc 2", "address": "Addr 2", "capacity": 2000},
        headers=admin_headers,
    ).json()

    # Create 2 products
    p1 = client.post(
        "/api/v1/products",
        json={"name": "Item 1", "sku": "ITEM-01", "unit_price": 10.0},
        headers=admin_headers,
    ).json()
    p2 = client.post(
        "/api/v1/products",
        json={"name": "Item 2", "sku": "ITEM-02", "unit_price": 20.0},
        headers=admin_headers,
    ).json()

    # Create 3 inventory records: (W1, P1), (W1, P2), (W2, P1)
    client.post("/api/v1/inventory", json={"warehouse_id": w1["id"], "product_id": p1["id"], "quantity": 10}, headers=admin_headers)
    client.post("/api/v1/inventory", json={"warehouse_id": w1["id"], "product_id": p2["id"], "quantity": 20}, headers=admin_headers)
    client.post("/api/v1/inventory", json={"warehouse_id": w2["id"], "product_id": p1["id"], "quantity": 30}, headers=admin_headers)

    # 1. Get all (Viewer role)
    all_res = client.get("/api/v1/inventory", headers=viewer_headers)
    assert all_res.status_code == status.HTTP_200_OK
    assert len(all_res.json()) == 3

    # 2. Filter by warehouse_id=W1
    w1_res = client.get(f"/api/v1/inventory?warehouse_id={w1['id']}", headers=viewer_headers)
    assert w1_res.status_code == status.HTTP_200_OK
    assert len(w1_res.json()) == 2

    # 3. Filter by product_id=P1
    p1_res = client.get(f"/api/v1/inventory?product_id={p1['id']}", headers=viewer_headers)
    assert p1_res.status_code == status.HTTP_200_OK
    assert len(p1_res.json()) == 2

    # 4. Filter by both warehouse_id=W2 and product_id=P1
    both_res = client.get(
        f"/api/v1/inventory?warehouse_id={w2['id']}&product_id={p1['id']}",
        headers=viewer_headers,
    )
    assert both_res.status_code == status.HTTP_200_OK
    assert len(both_res.json()) == 1
    assert both_res.json()[0]["quantity"] == 30


def test_get_inventory_pagination(client, admin_headers, viewer_headers, active_warehouse):
    # Create 3 products & inventory
    for i in range(1, 4):
        p = client.post(
            "/api/v1/products",
            json={"name": f"Prod {i}", "sku": f"SKU-PAGE-{i}", "unit_price": 5.0 * i},
            headers=admin_headers,
        ).json()
        client.post(
            "/api/v1/inventory",
            json={"warehouse_id": active_warehouse["id"], "product_id": p["id"], "quantity": 10 * i},
            headers=admin_headers,
        )

    # Limit=1
    page1 = client.get("/api/v1/inventory?limit=1", headers=viewer_headers)
    assert page1.status_code == status.HTTP_200_OK
    assert len(page1.json()) == 1

    # Skip=1, Limit=1
    page2 = client.get("/api/v1/inventory?skip=1&limit=1", headers=viewer_headers)
    assert page2.status_code == status.HTTP_200_OK
    assert len(page2.json()) == 1
    assert page2.json()[0]["id"] != page1.json()[0]["id"]


def test_get_inventory_by_id(client, admin_headers, driver_headers, active_warehouse, active_product):
    create_res = client.post(
        "/api/v1/inventory",
        json={"warehouse_id": active_warehouse["id"], "product_id": active_product["id"], "quantity": 77},
        headers=admin_headers,
    )
    inv_id = create_res.json()["id"]

    # Driver can retrieve inventory by ID
    get_res = client.get(f"/api/v1/inventory/{inv_id}", headers=driver_headers)
    assert get_res.status_code == status.HTTP_200_OK
    assert get_res.json()["id"] == inv_id
    assert get_res.json()["quantity"] == 77


def test_get_inventory_not_found(client, viewer_headers):
    res = client.get("/api/v1/inventory/99999", headers=viewer_headers)
    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in res.json()["detail"].lower()


# ------------------------------------------------------------------------------
# 3. Update Inventory Tests
# ------------------------------------------------------------------------------
def test_update_inventory_as_admin(client, admin_headers, active_warehouse, active_product):
    create_res = client.post(
        "/api/v1/inventory",
        json={"warehouse_id": active_warehouse["id"], "product_id": active_product["id"], "quantity": 50, "reorder_level": 10},
        headers=admin_headers,
    )
    inv_id = create_res.json()["id"]

    update_payload = {"quantity": 120, "reorder_level": 30}
    put_res = client.put(f"/api/v1/inventory/{inv_id}", json=update_payload, headers=admin_headers)
    assert put_res.status_code == status.HTTP_200_OK
    data = put_res.json()
    assert data["quantity"] == 120
    assert data["reorder_level"] == 30


def test_update_inventory_as_manager(client, admin_headers, manager_headers, active_warehouse, active_product):
    create_res = client.post(
        "/api/v1/inventory",
        json={"warehouse_id": active_warehouse["id"], "product_id": active_product["id"], "quantity": 40},
        headers=admin_headers,
    )
    inv_id = create_res.json()["id"]

    patch_res = client.patch(
        f"/api/v1/inventory/{inv_id}",
        json={"quantity": 95},
        headers=manager_headers,
    )
    assert patch_res.status_code == status.HTTP_200_OK
    assert patch_res.json()["quantity"] == 95


def test_update_inventory_negative_quantity(client, admin_headers, active_warehouse, active_product):
    create_res = client.post(
        "/api/v1/inventory",
        json={"warehouse_id": active_warehouse["id"], "product_id": active_product["id"], "quantity": 50},
        headers=admin_headers,
    )
    inv_id = create_res.json()["id"]

    res = client.patch(f"/api/v1/inventory/{inv_id}", json={"quantity": -20}, headers=admin_headers)
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_update_inventory_rejected_for_driver_and_viewer(client, admin_headers, driver_headers, viewer_headers, active_warehouse, active_product):
    create_res = client.post(
        "/api/v1/inventory",
        json={"warehouse_id": active_warehouse["id"], "product_id": active_product["id"], "quantity": 50},
        headers=admin_headers,
    )
    inv_id = create_res.json()["id"]

    assert client.put(f"/api/v1/inventory/{inv_id}", json={"quantity": 100}, headers=driver_headers).status_code == status.HTTP_403_FORBIDDEN
    assert client.put(f"/api/v1/inventory/{inv_id}", json={"quantity": 100}, headers=viewer_headers).status_code == status.HTTP_403_FORBIDDEN


def test_update_inventory_not_found(client, admin_headers):
    res = client.put("/api/v1/inventory/99999", json={"quantity": 10}, headers=admin_headers)
    assert res.status_code == status.HTTP_404_NOT_FOUND


# ------------------------------------------------------------------------------
# 4. Delete Inventory Tests
# ------------------------------------------------------------------------------
def test_delete_inventory_as_admin(client, admin_headers, viewer_headers, active_warehouse, active_product):
    create_res = client.post(
        "/api/v1/inventory",
        json={"warehouse_id": active_warehouse["id"], "product_id": active_product["id"], "quantity": 60},
        headers=admin_headers,
    )
    inv_id = create_res.json()["id"]

    del_res = client.delete(f"/api/v1/inventory/{inv_id}", headers=admin_headers)
    assert del_res.status_code == status.HTTP_200_OK
    assert "deleted successfully" in del_res.json()["message"]

    # Subsequent GET returns 404
    get_res = client.get(f"/api/v1/inventory/{inv_id}", headers=viewer_headers)
    assert get_res.status_code == status.HTTP_404_NOT_FOUND


def test_delete_inventory_rejected_for_manager(client, admin_headers, manager_headers, active_warehouse, active_product):
    create_res = client.post(
        "/api/v1/inventory",
        json={"warehouse_id": active_warehouse["id"], "product_id": active_product["id"], "quantity": 60},
        headers=admin_headers,
    )
    inv_id = create_res.json()["id"]

    del_res = client.delete(f"/api/v1/inventory/{inv_id}", headers=manager_headers)
    assert del_res.status_code == status.HTTP_403_FORBIDDEN


def test_delete_inventory_rejected_for_driver_and_viewer(client, admin_headers, driver_headers, viewer_headers, active_warehouse, active_product):
    create_res = client.post(
        "/api/v1/inventory",
        json={"warehouse_id": active_warehouse["id"], "product_id": active_product["id"], "quantity": 60},
        headers=admin_headers,
    )
    inv_id = create_res.json()["id"]

    assert client.delete(f"/api/v1/inventory/{inv_id}", headers=driver_headers).status_code == status.HTTP_403_FORBIDDEN
    assert client.delete(f"/api/v1/inventory/{inv_id}", headers=viewer_headers).status_code == status.HTTP_403_FORBIDDEN


def test_delete_inventory_not_found(client, admin_headers):
    res = client.delete("/api/v1/inventory/99999", headers=admin_headers)
    assert res.status_code == status.HTTP_404_NOT_FOUND
