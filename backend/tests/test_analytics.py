"""
FlowGrid - Analytics and Dashboard Backend Tests (Phase 22)
==========================================================
Comprehensive test suite validating:
- Overview statistics across empty and populated datasets (including vehicles & delivery KPIs).
- Shipment status distribution, date grouping, completion rate, on-time rates, and delay metrics.
- Inventory gross balances, safety threshold detection, and warehouse breakdowns.
- Warehouse network profiles, active vs inactive counts, capacity utilization, and storage summaries.
- Route status distribution, corridor throughput, and shipment assignment density.
- Fleet driver analytics (workforce status distribution, active accounts, driver utilization, active shipment count).
- Fleet vehicle analytics (status distribution, vehicle types, fleet capacity, vehicle utilization, active shipment count).
- Delivery performance (on-time rate, late rate, average duration, average delay duration, delay signals).
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
from app.models.vehicle import Vehicle
from app.models.route import Route, RouteStatus, RouteShipment
from app.models.tracking import ShipmentStatusHistory
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
        # 1. Warehouses: 2 active, 1 inactive (active capacity = 125,000)
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

        # 4. Drivers: 2 drivers (1 AVAILABLE, 1 ON_DUTY)
        u_drv1 = User(email="driver_inst@flowgrid.io", hashed_password="pw", name="Fleet Driver One", role=UserRole.DRIVER, is_active=True)
        u_drv2 = User(email="driver2_inst@flowgrid.io", hashed_password="pw", name="Fleet Driver Two", role=UserRole.DRIVER, is_active=True)
        db.add_all([u_drv1, u_drv2])
        db.commit()
        db.refresh(u_drv1)
        db.refresh(u_drv2)

        d1 = Driver(user_id=u_drv1.id, license_number="DL-88219", phone_number="+1-555-0192", availability_status="AVAILABLE")
        d2 = Driver(user_id=u_drv2.id, license_number="DL-99320", phone_number="+1-555-0193", availability_status="ON_DUTY")
        db.add_all([d1, d2])
        db.commit()
        db.refresh(d1)
        db.refresh(d2)

        # 5. Vehicles: 2 vehicles (1 AVAILABLE Van, 1 IN_USE Semi-Trailer)
        v1 = Vehicle(registration_number="TRK-VAN-101", vehicle_type="Van", capacity=Decimal("3000.00"), status="AVAILABLE")
        v2 = Vehicle(registration_number="TRK-SEMI-202", vehicle_type="Semi-Trailer", capacity=Decimal("15000.00"), status="IN_USE")
        db.add_all([v1, v2])
        db.commit()
        db.refresh(v1)
        db.refresh(v2)

        # 6. Routes:
        # r1: ACTIVE (Midwest Freight, est duration 8.0 hrs)
        # r2: COMPLETED (Northeast Express, est duration 6.0 hrs)
        r1 = Route(name="Midwest Freight", origin="Chicago, IL", destination="Cleveland, OH", estimated_duration=Decimal("8.00"), status=RouteStatus.ACTIVE, is_active=True)
        r2 = Route(name="Northeast Express", origin="Newark, NJ", destination="Boston, MA", estimated_duration=Decimal("6.00"), status=RouteStatus.COMPLETED, is_active=True)
        db.add_all([r1, r2])
        db.commit()
        db.refresh(r1)
        db.refresh(r2)

        # 7. Shipments:
        # s1: CREATED (assigned to d1, v1)
        # s2: IN_TRANSIT (assigned to d2, v2)
        # s3: DELIVERED (On-time: 5.0 hrs duration vs 6.0 planned)
        # s4: FAILED (Delay exception)
        # s5: CANCELLED
        # s6: DELIVERED (Late: 10.0 hrs duration vs 6.0 planned)
        pickup_t1 = datetime(2026, 9, 20, 8, 0, 0, tzinfo=timezone.utc)
        delivery_t1 = datetime(2026, 9, 20, 13, 0, 0, tzinfo=timezone.utc)  # 5.0 hrs

        pickup_t2 = datetime(2026, 9, 20, 7, 0, 0, tzinfo=timezone.utc)
        delivery_t2 = datetime(2026, 9, 20, 17, 0, 0, tzinfo=timezone.utc)  # 10.0 hrs

        s1 = Shipment(
            tracking_number="FG-ANALYTICS-001",
            origin_warehouse_id=w1.id,
            destination_address="100 Main St",
            destination_city="Detroit",
            destination_state="MI",
            destination_postal_code="48201",
            assigned_driver_id=d1.id,
            assigned_vehicle_id=v1.id,
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
            assigned_driver_id=d2.id,
            assigned_vehicle_id=v2.id,
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
            scheduled_pickup_at=pickup_t1,
            delivered_at=delivery_t1,
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
        s6 = Shipment(
            tracking_number="FG-ANALYTICS-006",
            origin_warehouse_id=w2.id,
            destination_address="600 Common St",
            destination_city="Boston",
            destination_state="MA",
            destination_postal_code="02102",
            scheduled_pickup_at=pickup_t2,
            delivered_at=delivery_t2,
            status=ShipmentStatus.DELIVERED,
            is_active=True,
        )
        db.add_all([s1, s2, s3, s4, s5, s6])
        db.commit()
        db.refresh(s1)
        db.refresh(s2)
        db.refresh(s3)
        db.refresh(s6)

        # 8. Route Shipments:
        # r1 has s1, s2
        # r2 has s3, s6
        rs1 = RouteShipment(route_id=r1.id, shipment_id=s1.id)
        rs2 = RouteShipment(route_id=r1.id, shipment_id=s2.id)
        rs3 = RouteShipment(route_id=r2.id, shipment_id=s3.id)
        rs6 = RouteShipment(route_id=r2.id, shipment_id=s6.id)
        db.add_all([rs1, rs2, rs3, rs6])
        db.commit()

        # 9. Status history milestones for delivered shipments
        h1 = ShipmentStatusHistory(
            shipment_id=s3.id,
            previous_status=ShipmentStatus.ASSIGNED,
            new_status=ShipmentStatus.PICKED_UP,
            created_at=pickup_t1,
        )
        h2 = ShipmentStatusHistory(
            shipment_id=s3.id,
            previous_status=ShipmentStatus.PICKED_UP,
            new_status=ShipmentStatus.DELIVERED,
            created_at=delivery_t1,
        )
        h3 = ShipmentStatusHistory(
            shipment_id=s6.id,
            previous_status=ShipmentStatus.ASSIGNED,
            new_status=ShipmentStatus.PICKED_UP,
            created_at=pickup_t2,
        )
        h4 = ShipmentStatusHistory(
            shipment_id=s6.id,
            previous_status=ShipmentStatus.PICKED_UP,
            new_status=ShipmentStatus.DELIVERED,
            created_at=delivery_t2,
            remarks="Heavy traffic and weather delay",
        )
        db.add_all([h1, h2, h3, h4])
        db.commit()

        yield {
            "warehouses": [w1, w2, w3],
            "products": [p1, p2, p3],
            "shipments": [s1, s2, s3, s4, s5, s6],
            "routes": [r1, r2],
            "drivers": [d1, d2],
            "vehicles": [v1, v2],
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
    assert data["total_vehicles"] == 0
    assert data["available_vehicles"] == 0
    assert data["on_time_delivery_rate"] == 0.0
    assert data["average_delivery_duration_hours"] is None
    assert data["average_delay_duration_hours"] is None
    assert data["overall_warehouse_utilization_rate"] == 0.0


def test_overview_populated_database(client, admin_headers, populated_db):
    """Populated database returns accurate counts and computed Phase 22 metrics."""
    res = client.get("/api/v1/analytics/overview", headers=admin_headers)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["total_shipments"] == 6
    assert data["active_shipments"] == 2  # s1 (CREATED) + s2 (IN_TRANSIT)
    assert data["delivered_shipments"] == 2  # s3 and s6
    assert data["delayed_or_failed_shipments"] == 1  # s4 (FAILED)
    assert data["total_warehouses"] == 3
    assert data["total_products"] == 3
    assert data["total_drivers"] == 2
    assert data["active_routes"] == 1  # r1 (ACTIVE)
    assert data["total_vehicles"] == 2
    assert data["available_vehicles"] == 1
    # 1 of 2 delivered shipments on-time (5.0 hrs <= 6.0 planned) -> 50.0%
    assert data["on_time_delivery_rate"] == 50.0
    # Average delivery duration: (5.0 + 10.0) / 2 = 7.5 hrs
    assert data["average_delivery_duration_hours"] == 7.5
    # Average delay duration for late shipments (s6: 10.0 - 6.0 = 4.0 hrs)
    assert data["average_delay_duration_hours"] == 4.0
    # Total stock: 5 + 20 + 50 = 75 units. Active capacity = 50000 + 75000 = 125,000.
    # Utilization: (75 / 125,000) * 100 = 0.06%
    assert data["overall_warehouse_utilization_rate"] == 0.06


# ==============================================================================
# 2. Shipment Analytics Tests
# ==============================================================================

def test_shipment_analytics_empty(client, admin_headers):
    """Empty shipment analytics returns valid structure with 0% completion rate."""
    res = client.get("/api/v1/analytics/shipments", headers=admin_headers)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["total_shipments"] == 0
    assert data["active_shipments"] == 0
    assert data["delivery_completion_rate"] == 0.0
    assert data["on_time_delivery_rate"] == 0.0
    assert data["late_delivery_rate"] == 0.0
    assert data["average_delivery_duration_hours"] is None
    assert data["average_delay_duration_hours"] is None
    assert data["historical_delay_frequency_rate"] == 0.0
    assert data["cancelled_shipments"] == 0
    assert data["returned_shipments"] == 0
    assert isinstance(data["by_status"], dict)
    assert isinstance(data["by_date"], list)


def test_shipment_analytics_populated(client, admin_headers, populated_db):
    """Verifies shipment distribution by status, date grouping, on-time rates, and delay metrics."""
    res = client.get("/api/v1/analytics/shipments", headers=admin_headers)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["total_shipments"] == 6
    assert data["active_shipments"] == 2  # CREATED + IN_TRANSIT
    assert data["by_status"]["CREATED"] == 1
    assert data["by_status"]["IN_TRANSIT"] == 1
    assert data["by_status"]["DELIVERED"] == 2
    assert data["by_status"]["FAILED"] == 1
    assert data["by_status"]["CANCELLED"] == 1
    assert data["cancelled_shipments"] == 1
    assert data["returned_shipments"] == 0
    # 2 delivered out of 6 = 33.33%
    assert data["delivery_completion_rate"] == 33.33
    # 1 on-time out of 2 delivered = 50.0%
    assert data["on_time_delivery_rate"] == 50.0
    assert data["late_delivery_rate"] == 50.0
    assert data["average_delivery_duration_hours"] == 7.5
    assert data["average_delay_duration_hours"] == 4.0
    # Delay signals: s4 (FAILED) + s6 (remark contains 'delay') = 2 shipments out of 6 = 33.33%
    assert data["historical_delay_frequency_rate"] == 33.33
    assert len(data["by_date"]) >= 1


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
    assert data["total_capacity"] == 0
    assert data["total_inventory_quantity"] == 0
    assert data["overall_capacity_utilization_rate"] == 0.0
    assert data["low_stock_items_count"] == 0
    assert data["warehouses_summary"] == []


def test_warehouse_analytics_populated(client, admin_headers, populated_db):
    """Verifies active/inactive warehouse counts and capacity profiles."""
    res = client.get("/api/v1/analytics/warehouses", headers=admin_headers)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["total_warehouses"] == 3
    assert data["active_warehouses"] == 2
    assert data["inactive_warehouses"] == 1
    assert data["total_capacity"] == 125000  # 50000 + 75000
    assert data["total_inventory_quantity"] == 75
    assert data["overall_capacity_utilization_rate"] == 0.06
    assert data["low_stock_items_count"] == 1
    assert len(data["warehouses_summary"]) == 3

    chicago = next(w for w in data["warehouses_summary"] if w["name"] == "Chicago Hub")
    assert chicago["is_active"] is True
    assert chicago["capacity"] == 50000
    assert chicago["total_products"] == 2
    assert chicago["total_stock_quantity"] == 25
    assert chicago["low_stock_items"] == 1
    assert chicago["capacity_utilization_rate"] == 0.05

    dallas = next(w for w in data["warehouses_summary"] if w["name"] == "Dallas Hub")
    assert dallas["is_active"] is False
    assert dallas["total_products"] == 0
    assert dallas["total_stock_quantity"] == 0
    assert dallas["capacity_utilization_rate"] == 0.0


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
    assert data["total_shipments_assigned"] == 4
    assert len(data["routes_summary"]) == 2

    midwest = next(r for r in data["routes_summary"] if r["name"] == "Midwest Freight")
    assert midwest["shipments_assigned_count"] == 2
    assert midwest["status"] == "ACTIVE"

    northeast = next(r for r in data["routes_summary"] if r["name"] == "Northeast Express")
    assert northeast["shipments_assigned_count"] == 2
    assert northeast["status"] == "COMPLETED"


# ==============================================================================
# 6. Driver Analytics Tests (Phase 22)
# ==============================================================================

def test_driver_analytics_empty(client, admin_headers):
    """Empty driver analytics returns zeros and empty summary safely."""
    res = client.get("/api/v1/analytics/drivers", headers=admin_headers)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["total_drivers"] == 0
    assert data["active_drivers"] == 0
    assert data["available_drivers"] == 0
    assert data["on_duty_drivers"] == 0
    assert data["in_transit_drivers"] == 0
    assert data["off_duty_drivers"] == 0
    assert data["suspended_drivers"] == 0
    assert data["driver_utilization_rate"] == 0.0
    assert data["drivers_summary"] == []


def test_driver_analytics_populated(client, admin_headers, populated_db):
    """Verifies driver status breakdown, utilization rate, and active shipment assignment counts."""
    res = client.get("/api/v1/analytics/drivers", headers=admin_headers)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["total_drivers"] == 2
    assert data["active_drivers"] == 2
    assert data["available_drivers"] == 1
    assert data["on_duty_drivers"] == 1
    assert data["in_transit_drivers"] == 0
    # Utilization: (1 ON_DUTY / 2 active) * 100 = 50.0%
    assert data["driver_utilization_rate"] == 50.0
    assert data["by_status"]["AVAILABLE"] == 1
    assert data["by_status"]["ON_DUTY"] == 1
    assert len(data["drivers_summary"]) == 2

    d1_summary = next(d for d in data["drivers_summary"] if d["license_number"] == "DL-88219")
    assert d1_summary["name"] == "Fleet Driver One"
    assert d1_summary["availability_status"] == "AVAILABLE"
    assert d1_summary["is_active"] is True
    assert d1_summary["active_shipments_count"] == 1  # s1 (CREATED)

    d2_summary = next(d for d in data["drivers_summary"] if d["license_number"] == "DL-99320")
    assert d2_summary["name"] == "Fleet Driver Two"
    assert d2_summary["availability_status"] == "ON_DUTY"
    assert d2_summary["is_active"] is True
    assert d2_summary["active_shipments_count"] == 1  # s2 (IN_TRANSIT)


# ==============================================================================
# 7. Vehicle Analytics Tests (Phase 22)
# ==============================================================================

def test_vehicle_analytics_empty(client, admin_headers):
    """Empty vehicle analytics returns zeros and empty summary safely."""
    res = client.get("/api/v1/analytics/vehicles", headers=admin_headers)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["total_vehicles"] == 0
    assert data["available_vehicles"] == 0
    assert data["in_use_vehicles"] == 0
    assert data["maintenance_vehicles"] == 0
    assert data["decommissioned_vehicles"] == 0
    assert data["total_fleet_capacity_kg"] == 0.0
    assert data["vehicle_utilization_rate"] == 0.0
    assert data["by_status"] == {"AVAILABLE": 0, "IN_USE": 0, "MAINTENANCE": 0, "DECOMMISSIONED": 0}
    assert data["by_type"] == {}
    assert data["vehicles_summary"] == []


def test_vehicle_analytics_populated(client, admin_headers, populated_db):
    """Verifies vehicle status breakdown, capacity, utilization, and type distribution."""
    res = client.get("/api/v1/analytics/vehicles", headers=admin_headers)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["total_vehicles"] == 2
    assert data["available_vehicles"] == 1
    assert data["in_use_vehicles"] == 1
    assert data["maintenance_vehicles"] == 0
    assert data["decommissioned_vehicles"] == 0
    # Capacity: 3000 + 15000 = 18,000 kg
    assert data["total_fleet_capacity_kg"] == 18000.0
    # Utilization: (1 IN_USE / 2 total) * 100 = 50.0%
    assert data["vehicle_utilization_rate"] == 50.0
    assert data["by_status"]["AVAILABLE"] == 1
    assert data["by_status"]["IN_USE"] == 1
    assert data["by_type"]["Van"] == 1
    assert data["by_type"]["Semi-Trailer"] == 1
    assert len(data["vehicles_summary"]) == 2

    van = next(v for v in data["vehicles_summary"] if v["registration_number"] == "TRK-VAN-101")
    assert van["vehicle_type"] == "Van"
    assert van["capacity_kg"] == 3000.0
    assert van["status"] == "AVAILABLE"
    assert van["active_shipments_count"] == 1  # s1 (CREATED)

    semi = next(v for v in data["vehicles_summary"] if v["registration_number"] == "TRK-SEMI-202")
    assert semi["vehicle_type"] == "Semi-Trailer"
    assert semi["capacity_kg"] == 15000.0
    assert semi["status"] == "IN_USE"
    assert semi["active_shipments_count"] == 1  # s2 (IN_TRANSIT)


# ==============================================================================
# 8. RBAC & Authenticated Access Tests
# ==============================================================================

def test_all_authenticated_roles_access(client, admin_headers, manager_headers, driver_headers, viewer_headers, populated_db):
    """ADMIN, MANAGER, DRIVER, and VIEWER can access all analytics endpoints."""
    endpoints = [
        "/api/v1/analytics/overview",
        "/api/v1/analytics/shipments",
        "/api/v1/analytics/inventory",
        "/api/v1/analytics/warehouses",
        "/api/v1/analytics/routes",
        "/api/v1/analytics/drivers",
        "/api/v1/analytics/vehicles",
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
        "/api/v1/analytics/drivers",
        "/api/v1/analytics/vehicles",
    ]
    for ep in endpoints:
        res = client.get(ep)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED, f"Expected 401 for {ep}"


# ==============================================================================
# 9. Date Filter & Range Validation Tests
# ==============================================================================

def test_date_filter_valid_range(client, admin_headers, populated_db):
    """Date filtering restricts metrics to matching window."""
    today = date.today()
    tomorrow = today + timedelta(days=1)
    yesterday = today - timedelta(days=1)

    # Filter spanning today: returns the 6 shipments
    res = client.get(
        f"/api/v1/analytics/shipments?start_date={yesterday.isoformat()}&end_date={tomorrow.isoformat()}",
        headers=admin_headers,
    )
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["total_shipments"] == 6

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
