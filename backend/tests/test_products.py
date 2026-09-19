"""
FlowGrid - Product Management Backend Tests
==========================================
Comprehensive test suite validating:
- Product CRUD operations with layered architecture (Repository, Service, Endpoint).
- Role-Based Access Control (RBAC):
  * Create: ADMIN, MANAGER allowed; DRIVER, VIEWER forbidden (403).
  * Read (all & by ID): All authenticated roles allowed.
  * Update (PUT & PATCH): ADMIN, MANAGER allowed; DRIVER, VIEWER forbidden (403).
  * Delete (soft-delete): ADMIN only; MANAGER, DRIVER, VIEWER forbidden (403).
- Input validation (unit_price >= 0.00, required name/SKU lengths).
- Consistent SKU case normalization and duplicate SKU safety (HTTP 400).
- 404 Not Found handling for non-existent product entities.
- Pagination and active-status filtering.
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
    return get_auth_headers_for_role(client, "admin_prod@flowgrid.io", "ADMIN")


@pytest.fixture
def manager_headers(client):
    return get_auth_headers_for_role(client, "manager_prod@flowgrid.io", "MANAGER")


@pytest.fixture
def driver_headers(client):
    return get_auth_headers_for_role(client, "driver_prod@flowgrid.io", "DRIVER")


@pytest.fixture
def viewer_headers(client):
    return get_auth_headers_for_role(client, "viewer_prod@flowgrid.io", "VIEWER")


SAMPLE_PRODUCT_PAYLOAD = {
    "name": "Industrial Hydraulic Pallet Jack 2500kg",
    "sku": "PLT-JK-2500",
    "description": "Heavy-duty steel manual hydraulic pallet truck with polyurethane wheels.",
    "unit_price": 389.50,
    "is_active": True,
}


# ------------------------------------------------------------------------------
# 1. Create Product Tests
# ------------------------------------------------------------------------------
def test_create_product_as_admin(client, admin_headers):
    response = client.post(
        "/api/v1/products",
        json=SAMPLE_PRODUCT_PAYLOAD,
        headers=admin_headers,
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == SAMPLE_PRODUCT_PAYLOAD["name"]
    assert data["sku"] == "PLT-JK-2500"
    assert data["description"] == SAMPLE_PRODUCT_PAYLOAD["description"]
    assert Decimal(str(data["unit_price"])) == Decimal("389.50")
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_product_as_manager(client, manager_headers):
    payload = {
        "name": "Barcode Inventory Scanner Wireless",
        "sku": "SCN-WL-01",
        "description": "2D Bluetooth handheld scanner with charging cradle.",
        "unit_price": 149.99,
        "is_active": True,
    }
    response = client.post(
        "/api/v1/products",
        json=payload,
        headers=manager_headers,
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["name"] == "Barcode Inventory Scanner Wireless"
    assert response.json()["sku"] == "SCN-WL-01"


def test_create_product_rejected_for_driver(client, driver_headers):
    response = client.post(
        "/api/v1/products",
        json=SAMPLE_PRODUCT_PAYLOAD,
        headers=driver_headers,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "Access forbidden" in response.json()["detail"]


def test_create_product_rejected_for_viewer(client, viewer_headers):
    response = client.post(
        "/api/v1/products",
        json=SAMPLE_PRODUCT_PAYLOAD,
        headers=viewer_headers,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "Access forbidden" in response.json()["detail"]


def test_create_product_unauthenticated(client):
    response = client.post("/api/v1/products", json=SAMPLE_PRODUCT_PAYLOAD)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_product_duplicate_sku(client, admin_headers):
    # First product
    res1 = client.post(
        "/api/v1/products",
        json=SAMPLE_PRODUCT_PAYLOAD,
        headers=admin_headers,
    )
    assert res1.status_code == status.HTTP_201_CREATED

    # Attempt to create product with duplicate SKU (case variation)
    duplicate_payload = {
        **SAMPLE_PRODUCT_PAYLOAD,
        "name": "Duplicate Jack",
        "sku": "plt-jk-2500",  # Lowercase test
    }
    res2 = client.post(
        "/api/v1/products",
        json=duplicate_payload,
        headers=admin_headers,
    )
    assert res2.status_code == status.HTTP_400_BAD_REQUEST
    assert "already exists" in res2.json()["detail"]


def test_create_product_invalid_unit_price(client, admin_headers):
    invalid_price_payload = {
        **SAMPLE_PRODUCT_PAYLOAD,
        "unit_price": -15.50,
    }
    response = client.post(
        "/api/v1/products",
        json=invalid_price_payload,
        headers=admin_headers,
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_product_validation_errors(client, admin_headers):
    # Missing required name
    no_name = {
        "sku": "NO-NAME-01",
        "unit_price": 50.00,
    }
    res1 = client.post("/api/v1/products", json=no_name, headers=admin_headers)
    assert res1.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Missing required SKU
    no_sku = {
        "name": "Product Without SKU",
        "unit_price": 20.00,
    }
    res2 = client.post("/api/v1/products", json=no_sku, headers=admin_headers)
    assert res2.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ------------------------------------------------------------------------------
# 2. Get Products Tests (All & By ID)
# ------------------------------------------------------------------------------
def test_get_all_products(client, admin_headers, viewer_headers):
    # Create two products
    client.post(
        "/api/v1/products",
        json={
            "name": "Heavy Duty Shelving Unit",
            "sku": "SHLV-HD-01",
            "unit_price": 199.00,
        },
        headers=admin_headers,
    )
    client.post(
        "/api/v1/products",
        json={
            "name": "Stretch Wrap Roll 500m",
            "sku": "WRAP-500M",
            "unit_price": 24.50,
        },
        headers=admin_headers,
    )

    # Viewer can list products
    res = client.get("/api/v1/products", headers=viewer_headers)
    assert res.status_code == status.HTTP_200_OK
    items = res.json()
    assert len(items) == 2
    assert items[0]["sku"] == "SHLV-HD-01"
    assert items[1]["sku"] == "WRAP-500M"


def test_get_products_pagination_and_filter(client, admin_headers, viewer_headers):
    client.post(
        "/api/v1/products",
        json={
            "name": "Active Product 1",
            "sku": "ACT-01",
            "unit_price": 10.00,
            "is_active": True,
        },
        headers=admin_headers,
    )
    client.post(
        "/api/v1/products",
        json={
            "name": "Inactive Product 2",
            "sku": "INACT-02",
            "unit_price": 20.00,
            "is_active": False,
        },
        headers=admin_headers,
    )

    # Filter active only
    active_res = client.get("/api/v1/products?is_active=true", headers=viewer_headers)
    assert active_res.status_code == status.HTTP_200_OK
    assert len(active_res.json()) == 1
    assert active_res.json()[0]["sku"] == "ACT-01"

    # Pagination limit=1
    limit_res = client.get("/api/v1/products?limit=1", headers=viewer_headers)
    assert limit_res.status_code == status.HTTP_200_OK
    assert len(limit_res.json()) == 1


def test_get_product_by_id(client, admin_headers, driver_headers):
    create_res = client.post(
        "/api/v1/products",
        json=SAMPLE_PRODUCT_PAYLOAD,
        headers=admin_headers,
    )
    product_id = create_res.json()["id"]

    # Driver can retrieve product by ID
    get_res = client.get(f"/api/v1/products/{product_id}", headers=driver_headers)
    assert get_res.status_code == status.HTTP_200_OK
    assert get_res.json()["id"] == product_id
    assert get_res.json()["sku"] == "PLT-JK-2500"


def test_get_product_not_found(client, viewer_headers):
    response = client.get("/api/v1/products/99999", headers=viewer_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"].lower()


# ------------------------------------------------------------------------------
# 3. Update Product Tests
# ------------------------------------------------------------------------------
def test_update_product_as_admin(client, admin_headers):
    create_res = client.post(
        "/api/v1/products",
        json=SAMPLE_PRODUCT_PAYLOAD,
        headers=admin_headers,
    )
    product_id = create_res.json()["id"]

    update_payload = {
        "name": "Industrial Hydraulic Pallet Jack 3000kg (Upgraded)",
        "unit_price": 429.00,
    }
    update_res = client.put(
        f"/api/v1/products/{product_id}",
        json=update_payload,
        headers=admin_headers,
    )
    assert update_res.status_code == status.HTTP_200_OK
    updated_data = update_res.json()
    assert updated_data["name"] == "Industrial Hydraulic Pallet Jack 3000kg (Upgraded)"
    assert Decimal(str(updated_data["unit_price"])) == Decimal("429.00")
    assert updated_data["sku"] == "PLT-JK-2500"


def test_update_product_as_manager(client, admin_headers, manager_headers):
    create_res = client.post(
        "/api/v1/products",
        json=SAMPLE_PRODUCT_PAYLOAD,
        headers=admin_headers,
    )
    product_id = create_res.json()["id"]

    patch_res = client.patch(
        f"/api/v1/products/{product_id}",
        json={"description": "Updated warranty 24 months."},
        headers=manager_headers,
    )
    assert patch_res.status_code == status.HTTP_200_OK
    assert patch_res.json()["description"] == "Updated warranty 24 months."


def test_update_product_duplicate_sku_conflict(client, admin_headers):
    # Create product 1
    client.post(
        "/api/v1/products",
        json={**SAMPLE_PRODUCT_PAYLOAD, "sku": "SKU-PROD-01"},
        headers=admin_headers,
    )
    # Create product 2
    res2 = client.post(
        "/api/v1/products",
        json={**SAMPLE_PRODUCT_PAYLOAD, "sku": "SKU-PROD-02"},
        headers=admin_headers,
    )
    prod2_id = res2.json()["id"]

    # Attempt to update product 2's SKU to SKU-PROD-01
    conflict_res = client.patch(
        f"/api/v1/products/{prod2_id}",
        json={"sku": "sku-prod-01"},
        headers=admin_headers,
    )
    assert conflict_res.status_code == status.HTTP_400_BAD_REQUEST
    assert "already exists" in conflict_res.json()["detail"]


def test_update_product_same_sku_allowed(client, admin_headers):
    create_res = client.post(
        "/api/v1/products",
        json=SAMPLE_PRODUCT_PAYLOAD,
        headers=admin_headers,
    )
    product_id = create_res.json()["id"]

    # Re-submitting the same SKU (case-insensitive) should succeed
    res = client.patch(
        f"/api/v1/products/{product_id}",
        json={"sku": "plt-jk-2500", "name": "Same SKU New Name"},
        headers=admin_headers,
    )
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["name"] == "Same SKU New Name"


def test_update_product_rejected_for_driver_and_viewer(
    client, admin_headers, driver_headers, viewer_headers
):
    create_res = client.post(
        "/api/v1/products",
        json=SAMPLE_PRODUCT_PAYLOAD,
        headers=admin_headers,
    )
    product_id = create_res.json()["id"]

    assert (
        client.put(
            f"/api/v1/products/{product_id}",
            json={"name": "Driver Hack"},
            headers=driver_headers,
        ).status_code
        == status.HTTP_403_FORBIDDEN
    )

    assert (
        client.put(
            f"/api/v1/products/{product_id}",
            json={"name": "Viewer Hack"},
            headers=viewer_headers,
        ).status_code
        == status.HTTP_403_FORBIDDEN
    )


def test_update_product_not_found(client, admin_headers):
    res = client.put(
        "/api/v1/products/99999",
        json={"name": "Non-existent"},
        headers=admin_headers,
    )
    assert res.status_code == status.HTTP_404_NOT_FOUND


def test_update_product_invalid_price(client, admin_headers):
    create_res = client.post(
        "/api/v1/products",
        json=SAMPLE_PRODUCT_PAYLOAD,
        headers=admin_headers,
    )
    product_id = create_res.json()["id"]

    res = client.patch(
        f"/api/v1/products/{product_id}",
        json={"unit_price": -5.00},
        headers=admin_headers,
    )
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ------------------------------------------------------------------------------
# 4. Delete Product Tests (Soft Delete)
# ------------------------------------------------------------------------------
def test_delete_product_as_admin_soft_deletes(client, admin_headers, viewer_headers):
    create_res = client.post(
        "/api/v1/products",
        json=SAMPLE_PRODUCT_PAYLOAD,
        headers=admin_headers,
    )
    product_id = create_res.json()["id"]

    delete_res = client.delete(
        f"/api/v1/products/{product_id}",
        headers=admin_headers,
    )
    assert delete_res.status_code == status.HTTP_200_OK
    assert delete_res.json()["is_active"] is False

    # Confirm soft-deleted state persists
    fetch_res = client.get(
        f"/api/v1/products/{product_id}",
        headers=viewer_headers,
    )
    assert fetch_res.status_code == status.HTTP_200_OK
    assert fetch_res.json()["is_active"] is False


def test_delete_product_rejected_for_manager(client, admin_headers, manager_headers):
    create_res = client.post(
        "/api/v1/products",
        json=SAMPLE_PRODUCT_PAYLOAD,
        headers=admin_headers,
    )
    product_id = create_res.json()["id"]

    del_res = client.delete(
        f"/api/v1/products/{product_id}",
        headers=manager_headers,
    )
    assert del_res.status_code == status.HTTP_403_FORBIDDEN


def test_delete_product_rejected_for_driver_and_viewer(
    client, admin_headers, driver_headers, viewer_headers
):
    create_res = client.post(
        "/api/v1/products",
        json=SAMPLE_PRODUCT_PAYLOAD,
        headers=admin_headers,
    )
    product_id = create_res.json()["id"]

    assert (
        client.delete(
            f"/api/v1/products/{product_id}", headers=driver_headers
        ).status_code
        == status.HTTP_403_FORBIDDEN
    )
    assert (
        client.delete(
            f"/api/v1/products/{product_id}", headers=viewer_headers
        ).status_code
        == status.HTTP_403_FORBIDDEN
    )


def test_delete_product_not_found(client, admin_headers):
    res = client.delete("/api/v1/products/99999", headers=admin_headers)
    assert res.status_code == status.HTTP_404_NOT_FOUND
