"""
FlowGrid - Analytics and Dashboard Backend Tests (Phase 12)
==========================================================
Comprehensive test suite validating:
- Overview statistics across empty and populated datasets.
- Shipment status distribution, date grouping, completion rate, and exception tracking.
- Inventory gross balances, safety threshold detection, and warehouse breakdowns.
- Warehouse network profiles, active vs inactive counts, and storage summaries.
- Route status distribution, corridor throughput, and shipment assignment density.
- Role-Based Access Control (RBAC):
  * Read access granted to all authenticated roles (ADMIN, MANAGER, DRIVER, VIEWER).
  * Rejection of unauthenticated requests with HTTP 401 Unauthorized.
- Date range filtering (start_date, end_date).
- Rejection of invalid date ranges (start_date > end_date) with HTTP 400 Bad Request.
"""

from datetime import datetime, date, timedelta, timezone
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
from app.models.shipment import Shipment, ShipmentStatus
from app.models.warehouse import Warehouse
from app.models.product import Product
from app.models.inventory import Inventory
from app.models.driver import Driver
from app.models.route import Route, RouteStatus, RouteShipment
from app.models.user import User, UserRole

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
    return get_auth_headers_for_role(client, "admin_analytics@flowgrid.io", "ADMIN")


@pytest.fixture
def manager_headers(client):
    return get_auth_headers_for_role(client, "manager_analytics@flowgrid.io", "MANAGER")


@pytest.fixture
def driver_headers(client):
    return get_auth_headers_for_role(client, "driver_analytics@flowgrid.io", "DRIVER")


@pytest.fixture
def viewer_headers(client):
    return get_auth_headers_for_role(client, "viewer_analytics@flowgrid.io", "VIEWER")


@pytest.fixture
def populated_db():
    """
    Populates the database with realistic sample entities across all models.
    """
    db = TestingSessionLocal()
    try:
        # 1. Warehouses: 2 active, 1 inactive
        w1 = Warehouse(name="Chicago Hub", location="Chicago, IL", address="100 Logistics Way", capacity=50000, is_active=True)
        w2 = Warehouse(name="Newark Hub", location="Newark, NJ", address="200 Freight Ave", capacity=75000, is_active=True)
        w3 = Warehouse(name="Dallas Hub", location="Dallas, TX", address="300 Transit Blvd", capacity=30000, is_active=False)
        db.add_all([w1, w2, w3])
        db.commit()
        db.refresh(w1)
        db.refresh(w2)
        db.refresh(w3)

        # 2. Products: 3 products
        p1 = Product(name="Industrial Sensor", sku="SKU-SENS-01", unit_price=Decimal("120.00"), is_active=True)
        p2 = Product(name="Control Module", sku="SKU-MOD-02", unit_price=Decimal("450.00"), is_active=True)
        p3 = Product(name="Power Supply", sku="SKU-PWR-03", unit_price=Decimal("85.00"), is_active=True)
        db.add_all([p1, p2, p3])
        db.commit()
        db.refresh(p1)
        db.refresh(p2)
        db.refresh(p3)

        # 3. Inventory:
        # w1: p1 qty=5, reorder=10 (LOW STOCK!)
        # w1: p2 qty=20, reorder=5 (NORMAL)
        # w2: p3 qty=50, reorder=15 (NORMAL)
        inv1 = Inventory(warehouse_id=w1.id, product_id=p1.id, quantity=5, reorder_level=10)
        inv2 = Inventory(warehouse_id=w1.id, product_id=p2.id, quantity=20, reorder_level=5)
        inv3 = Inventory(warehouse_id=w2.id, product_id=p3.id, quantity=50, reorder_level=15)
        db.add_all([inv1, inv2, inv3])
        db.commit()

        # 4. Driver
        u_drv = User(email="driver_inst@flowgrid.io", hashed_password="pw", name="Fleet Driver", role=UserRole.DRIVER, is_active=True)
        db.add(u_drv)
        db.commit()
        db.refresh(u_drv)
        d1 = Driver(user_id=u_drv.id, license_number="DL-88219", phone_number="+1-555-0192", availability_status="AVAILABLE")
        db.add(d1)
        db.commit()

        # 5. Shipments:
        # s1: CREATED
        # s2: IN_TRANSIT
        # s3: DELIVERED
        # s4: FAILED
        # s5: CANCELLED
        s1 = Shipment(
            tracking_number="FG-ANALYTICS-001",
            origin_warehouse_id=w1.id,
            destination_address="100 Main St",
            destination_city="Detroit",
            destination_state="MI",
            destination_postal_code="48201",
            status=ShipmentStatus.CREATED,
            is_active=True,
        )
        s2 = Shipment(
            tracking_number="FG-ANALYTICS-002",
            origin_warehouse_id=w1.id,
            destination_address="200 Park Ave",
            destination_city="Cleveland",
            destination_state="OH",
            destination_postal_code="44101",
            status=ShipmentStatus.IN_TRANSIT,
            is_active=True,
        )
        s3 = Shipment(
            tracking_number="FG-ANALYTICS-003",
            origin_warehouse_id=w2.id,
            destination_address="300 Broad St",
            destination_city="Boston",
            destination_state="MA",
            destination_postal_code="02101",
            status=ShipmentStatus.DELIVERED,
            is_active=True,
        )
        s4 = Shipment(
            tracking_number="FG-ANALYTICS-004",
            origin_warehouse_id=w2.id,
            destination_address="400 Elm St",
            destination_city="Philadelphia",
            destination_state="PA",
            destination_postal_code="19101",
            status=ShipmentStatus.FAILED,
            is_active=True,
        )
        s5 = Shipment(
            tracking_number="FG-ANALYTICS-005",
            origin_warehouse_id=w1.id,
            destination_address="500 Pine St",
            destination_city="Chicago",
            destination_state="IL",
            destination_postal_code="60601",
            status=ShipmentStatus.CANCELLED,
            is_active=True,
        )
        db.add_all([s1, s2, s3, s4, s5])
        db.commit()
        db.refresh(s1)
        db.refresh(s2)

        # 6. Routes:
        # r1: ACTIVE
        # r2: COMPLETED
        r1 = Route(name="Midwest Freight", origin="Chicago, IL", destination="Cleveland, OH", status=RouteStatus.ACTIVE, is_active=True)
        r2 = Route(name="Northeast Express", origin="Newark, NJ", destination="Boston, MA", status=RouteStatus.COMPLETED, is_active=True)
        db.add_all([r1, r2])
        db.commit()
        db.refresh(r1)
        db.refresh(r2)

        # 7. Route Shipments: assign s1 and s2 to r1
        rs1 = RouteShipment(route_id=r1.id, shipment_id=s1.id)
        rs2 = RouteShipment(route_id=r1.id, shipment_id=s2.id)
        db.add_all([rs1, rs2])
        db.commit()

        yield {
            "warehouses": [w1, w2, w3],
            "products": [p1, p2, p3],
            "shipments": [s1, s2, s3, s4, s5],
            "routes": [r1, r2],
        }
    finally:
        db.close()


# ==============================================================================
# 1. Overview Statistics Tests
# ==============================================================================

def test_overview_empty_database(client, admin_headers):
    """Empty database returns all zeros safely without error."""
    res = client.get("/api/v1/analytics/overview", headers=admin_headers)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["total_shipments"] == 0
    assert data["active_shipments"] == 0
    assert data["delivered_shipments"] == 0
    assert data["delayed_or_failed_shipments"] == 0
    assert data["total_warehouses"] == 0
    assert data["total_products"] == 0
    assert data["total_drivers"] == 0
    assert data["active_routes"] == 0


def test_overview_populated_database(client, admin_headers, populated_db):
    """Populated database returns accurate counts."""
    res = client.get("/api/v1/analytics/overview", headers=admin_headers)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["total_shipments"] == 5
    assert data["active_shipments"] == 2  # s1 (CREATED) + s2 (IN_TRANSIT)
    assert data["delivered_shipments"] == 1  # s3 (DELIVERED)
    assert data["delayed_or_failed_shipments"] == 1  # s4 (FAILED)
    assert data["total_warehouses"] == 3
    assert data["total_products"] == 3
    assert data["total_drivers"] == 1
    assert data["active_routes"] == 1  # r1 (ACTIVE)


# ==============================================================================
# 2. Shipment Analytics Tests
# ==============================================================================

def test_shipment_analytics_empty(client, admin_headers):
    """Empty shipment analytics returns valid structure with 0% completion rate."""
    res = client.get("/api/v1/analytics/shipments", headers=admin_headers)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["total_shipments"] == 0
    assert data["delivery_completion_rate"] == 0.0
    assert data["cancelled_shipments"] == 0
    assert data["returned_shipments"] == 0
    assert isinstance(data["by_status"], dict)
    assert isinstance(data["by_date"], list)


def test_shipment_analytics_populated(client, admin_headers, populated_db):
    """Verifies shipment distribution by status, date grouping, and completion rate."""
    res = client.get("/api/v1/analytics/shipments", headers=admin_headers)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["total_shipments"] == 5
    assert data["by_status"]["CREATED"] == 1
    assert data["by_status"]["IN_TRANSIT"] == 1
    assert data["by_status"]["DELIVERED"] == 1
    assert data["by_status"]["FAILED"] == 1
    assert data["by_status"]["CANCELLED"] == 1
    assert data["cancelled_shipments"] == 1
    assert data["returned_shipments"] == 0
    # 1 delivered out of 5 = 20.0%
    assert data["delivery_completion_rate"] == 20.0
    assert len(data["by_date"]) >= 1
    today_str = str(date.today())
    assert any(entry["date"] == today_str for entry in data["by_date"])


# ==============================================================================
# 3. Inventory Analytics Tests
# ==============================================================================

def test_inventory_analytics_empty(client, admin_headers):
    """Empty inventory analytics returns zeros and empty arrays."""
    res = client.get("/api/v1/analytics/inventory", headers=admin_headers)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["total_inventory_records"] == 0
    assert data["total_available_quantity"] == 0
    assert data["low_stock_products_count"] == 0
    assert data["low_stock_products"] == []
    assert data["by_warehouse"] == []


def test_inventory_analytics_populated(client, admin_headers, populated_db):
    """Verifies inventory quantities, low-stock alerts, and warehouse breakdown."""
    res = client.get("/api/v1/analytics/inventory", headers=admin_headers)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["total_inventory_records"] == 3
    # 5 + 20 + 50 = 75 units total
    assert data["total_available_quantity"] == 75
    # 1 low stock item: p1 at w1 (qty=5 <= reorder=10)
    assert data["low_stock_products_count"] == 1
    assert len(data["low_stock_products"]) == 1
    low_stock = data["low_stock_products"][0]
    assert low_stock["sku"] == "SKU-SENS-01"
    assert low_stock["quantity"] == 5
    assert low_stock["reorder_level"] == 10

    # Warehouse breakdown check
    assert len(data["by_warehouse"]) == 3
    w1_summary = next(w for w in data["by_warehouse"] if w["warehouse_name"] == "Chicago Hub")
    assert w1_summary["total_quantity"] == 25  # 5 + 20
    assert w1_summary["unique_products_count"] == 2
    assert w1_summary["low_stock_count"] == 1


# ==============================================================================
# 4. Warehouse Analytics Tests
# ==============================================================================

def test_warehouse_analytics_empty(client, admin_headers):
    """Empty warehouse analytics returns valid zeros and empty list."""
    res = client.get("/api/v1/analytics/warehouses", headers=admin_headers)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["total_warehouses"] == 0
    assert data["active_warehouses"] == 0
    assert data["inactive_warehouses"] == 0
    assert data["warehouses_summary"] == []


def test_warehouse_analytics_populated(client, admin_headers, populated_db):
    """Verifies active/inactive warehouse counts and capacity profiles."""
    res = client.get("/api/v1/analytics/warehouses", headers=admin_headers)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["total_warehouses"] == 3
    assert data["active_warehouses"] == 2
    assert data["inactive_warehouses"] == 1
    assert len(data["warehouses_summary"]) == 3

    chicago = next(w for w in data["warehouses_summary"] if w["name"] == "Chicago Hub")
    assert chicago["is_active"] is True
    assert chicago["capacity"] == 50000
    assert chicago["total_products"] == 2
    assert chicago["total_stock_quantity"] == 25
    assert chicago["low_stock_items"] == 1

    dallas = next(w for w in data["warehouses_summary"] if w["name"] == "Dallas Hub")
    assert dallas["is_active"] is False
    assert dallas["total_products"] == 0
    assert dallas["total_stock_quantity"] == 0


# ==============================================================================
# 5. Route Analytics Tests
# ==============================================================================

def test_route_analytics_empty(client, admin_headers):
    """Empty route analytics returns zeros and empty summary."""
    res = client.get("/api/v1/analytics/routes", headers=admin_headers)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["total_routes"] == 0
    assert data["active_routes"] == 0
    assert data["completed_routes"] == 0
    assert data["total_shipments_assigned"] == 0
    assert data["routes_summary"] == []


def test_route_analytics_populated(client, admin_headers, populated_db):
    """Verifies route status distribution and shipment assignments count."""
    res = client.get("/api/v1/analytics/routes", headers=admin_headers)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["total_routes"] == 2
    assert data["active_routes"] == 1
    assert data["completed_routes"] == 1
    assert data["by_status"]["ACTIVE"] == 1
    assert data["by_status"]["COMPLETED"] == 1
    assert data["total_shipments_assigned"] == 2
    assert len(data["routes_summary"]) == 2

    midwest = next(r for r in data["routes_summary"] if r["name"] == "Midwest Freight")
    assert midwest["shipments_assigned_count"] == 2
    assert midwest["status"] == "ACTIVE"

    northeast = next(r for r in data["routes_summary"] if r["name"] == "Northeast Express")
    assert northeast["shipments_assigned_count"] == 0
    assert northeast["status"] == "COMPLETED"


# ==============================================================================
# 6. RBAC & Authenticated Access Tests
# ==============================================================================

def test_all_authenticated_roles_access(client, admin_headers, manager_headers, driver_headers, viewer_headers, populated_db):
    """ADMIN, MANAGER, DRIVER, and VIEWER can access all analytics endpoints."""
    endpoints = [
        "/api/v1/analytics/overview",
        "/api/v1/analytics/shipments",
        "/api/v1/analytics/inventory",
        "/api/v1/analytics/warehouses",
        "/api/v1/analytics/routes",
    ]
    for headers in [admin_headers, manager_headers, driver_headers, viewer_headers]:
        for ep in endpoints:
            res = client.get(ep, headers=headers)
            assert res.status_code == status.HTTP_200_OK, f"Failed on {ep} with status {res.status_code}"


def test_unauthenticated_access_rejected(client):
    """Unauthenticated requests are rejected with 401 Unauthorized across all endpoints."""
    endpoints = [
        "/api/v1/analytics/overview",
        "/api/v1/analytics/shipments",
        "/api/v1/analytics/inventory",
        "/api/v1/analytics/warehouses",
        "/api/v1/analytics/routes",
    ]
    for ep in endpoints:
        res = client.get(ep)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED, f"Expected 401 for {ep}"


# ==============================================================================
# 7. Date Filter & Range Validation Tests
# ==============================================================================

def test_date_filter_valid_range(client, admin_headers, populated_db):
    """Date filtering restricts metrics to matching window."""
    today = date.today()
    tomorrow = today + timedelta(days=1)
    yesterday = today - timedelta(days=1)

    # Filter spanning today: returns the 5 shipments
    res = client.get(
        f"/api/v1/analytics/shipments?start_date={yesterday.isoformat()}&end_date={tomorrow.isoformat()}",
        headers=admin_headers,
    )
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["total_shipments"] == 5

    # Filter in past: returns 0 shipments
    past_start = today - timedelta(days=30)
    past_end = today - timedelta(days=20)
    res_past = client.get(
        f"/api/v1/analytics/shipments?start_date={past_start.isoformat()}&end_date={past_end.isoformat()}",
        headers=admin_headers,
    )
    assert res_past.status_code == status.HTTP_200_OK
    assert res_past.json()["total_shipments"] == 0


def test_date_filter_invalid_range_rejected(client, admin_headers):
    """start_date > end_date returns HTTP 400 Bad Request."""
    res = client.get(
        "/api/v1/analytics/overview?start_date=2026-09-30&end_date=2026-09-01",
        headers=admin_headers,
    )
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert "start_date cannot be after end_date" in res.json()["detail"]

    res_shipments = client.get(
        "/api/v1/analytics/shipments?start_date=2026-09-30&end_date=2026-09-01",
        headers=admin_headers,
    )
    assert res_shipments.status_code == status.HTTP_400_BAD_REQUEST
    assert "start_date cannot be after end_date" in res_shipments.json()["detail"]
