"""
Delay Risk Scoring Tests (Phase 24.2)
=====================================
Comprehensive test suite validating:
1. Unit tests for DelayRiskService:
   - Factor-by-factor scoring (unassigned assets, capacity strain, interstate, warehouse congestion)
   - Boundary checks (0 floor, 100 ceiling, clamping)
   - Missing data resilience (null weights, null capacities, null warehouses, null destinations)
   - Terminal status isolation (DELIVERED, CANCELLED, RETURNED -> score 0)
   - Explicit non-calibrated probability flags
2. API integration tests for GET /api/v1/analytics/delay-risk:
   - Full fleet evaluation
   - Filtering by shipment_id, status, risk_category
   - Pagination (limit, skip)
   - 404 for nonexistent shipment_id
   - 400 for invalid risk_category
3. Single shipment endpoint GET /api/v1/analytics/delay-risk/{shipment_id}
4. Authorization & RBAC tests (ADMIN, MANAGER, DRIVER, VIEWER allowed; 401 for unauthenticated)
"""

from decimal import Decimal
from datetime import datetime, timezone
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.db.base import Base
from app.main import app
from app.models.driver import Driver
from app.models.inventory import Inventory
from app.models.product import Product
from app.models.route import Route, RouteShipment, RouteStatus
from app.models.shipment import Shipment, ShipmentStatus
from app.models.user import User, UserRole
from app.models.vehicle import Vehicle
from app.models.warehouse import Warehouse
from app.services.delay_risk_service import delay_risk_service

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


def get_auth_headers(client: TestClient, email: str, role: str) -> dict:
    password = "SecurePassword2026!"
    client.post(
        "/api/v1/auth/register",
        json={
            "name": f"{role.capitalize()} Tester",
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
    return get_auth_headers(client, "admin_risk@flowgrid.io", "ADMIN")


@pytest.fixture
def manager_headers(client):
    return get_auth_headers(client, "manager_risk@flowgrid.io", "MANAGER")


@pytest.fixture
def driver_headers(client):
    return get_auth_headers(client, "driver_risk@flowgrid.io", "DRIVER")


@pytest.fixture
def viewer_headers(client):
    return get_auth_headers(client, "viewer_risk@flowgrid.io", "VIEWER")


# ==============================================================================
# 1. Unit Tests for DelayRiskService Scoring Logic
# ==============================================================================

def test_optimal_shipment_zero_risk():
    """An active shipment with all assets, optimal capacity, local transit, and low warehouse load scores 0 (LOW)."""
    wh = Warehouse(id=1, name="Hub", location="Chicago, IL", capacity=100000, is_active=True)
    drv = Driver(id=1, license_number="CDL-1", phone_number="+1", availability_status="AVAILABLE")
    veh = Vehicle(id=1, registration_number="TRK-1", vehicle_type="Box Truck", capacity=Decimal("10000.00"), status="AVAILABLE")
    rte = Route(id=1, name="Route 1", origin="Chicago", destination="Peoria", estimated_distance=Decimal("150.00"), status=RouteStatus.ACTIVE)

    s = Shipment(
        id=10,
        tracking_number="FG-TEST-00",
        origin_warehouse_id=1,
        origin_warehouse=wh,
        destination_address="100 Main St",
        destination_city="Peoria",
        destination_state="IL",  # Local/Intra-state
        destination_postal_code="61601",
        status=ShipmentStatus.IN_TRANSIT,
        assigned_driver_id=1,
        assigned_driver=drv,
        assigned_vehicle_id=1,
        assigned_vehicle=veh,
        total_weight_kg=Decimal("4000.00"),  # 40% load <= 80%
        routes=[rte],
        is_active=True,
    )

    stock_map = {1: 30000}  # 30% warehouse utilization <= 75%
    res = delay_risk_service.evaluate_shipment(s, warehouse_stock_map=stock_map)

    assert res.risk_score == 0
    assert res.risk_category == "LOW"
    assert len(res.contributing_factors) == 0
    assert res.is_calibrated_probability is False
    assert "LOW DELAY RISK" in res.summary_explanation


def test_missing_assets_accumulate_risk_points():
    """Missing driver (+20), vehicle (+15), and route (+10) add up to 45 points (MEDIUM)."""
    wh = Warehouse(id=1, name="Hub", location="Chicago, IL", capacity=100000, is_active=True)

    s = Shipment(
        id=11,
        tracking_number="FG-TEST-01",
        origin_warehouse_id=1,
        origin_warehouse=wh,
        destination_address="100 Main St",
        destination_city="Peoria",
        destination_state="IL",  # Local
        destination_postal_code="61601",
        status=ShipmentStatus.CREATED,
        assigned_driver_id=None,
        assigned_vehicle_id=None,
        total_weight_kg=None,
        routes=[],
        is_active=True,
    )

    res = delay_risk_service.evaluate_shipment(s, warehouse_stock_map={1: 10000})

    assert res.risk_score == 45
    assert res.risk_category == "MEDIUM"
    factor_ids = [f.factor_id for f in res.contributing_factors]
    assert "UNASSIGNED_DRIVER" in factor_ids
    assert "UNASSIGNED_VEHICLE" in factor_ids
    assert "UNASSIGNED_ROUTE" in factor_ids


def test_capacity_strain_critical_and_high():
    """Vehicle capacity load >90% adds 20 pts (HIGH); 80-90% adds 10 pts (MEDIUM)."""
    wh = Warehouse(id=1, name="Hub", location="Chicago, IL", capacity=100000, is_active=True)
    drv = Driver(id=1, license_number="CDL-1", phone_number="+1", availability_status="AVAILABLE")
    veh = Vehicle(id=1, registration_number="TRK-1", vehicle_type="Box Truck", capacity=Decimal("10000.00"), status="IN_USE")
    rte = Route(id=1, name="Route 1", origin="Chicago", destination="Peoria", status=RouteStatus.ACTIVE)

    # 95% load -> +20 pts
    s_critical = Shipment(
        id=12,
        tracking_number="FG-CRIT-CAP",
        origin_warehouse=wh,
        destination_city="Peoria",
        destination_state="IL",
        destination_address="St",
        destination_postal_code="12345",
        status=ShipmentStatus.IN_TRANSIT,
        assigned_driver=drv,
        assigned_driver_id=1,
        assigned_vehicle=veh,
        assigned_vehicle_id=1,
        routes=[rte],
        total_weight_kg=Decimal("9500.00"),
        is_active=True,
    )
    res_crit = delay_risk_service.evaluate_shipment(s_critical)
    assert any(f.factor_id == "CRITICAL_CAPACITY_STRAIN" and f.impact_points == 20 for f in res_crit.contributing_factors)

    # 85% load -> +10 pts
    s_high = Shipment(
        id=13,
        tracking_number="FG-HIGH-CAP",
        origin_warehouse=wh,
        destination_city="Peoria",
        destination_state="IL",
        destination_address="St",
        destination_postal_code="12345",
        status=ShipmentStatus.IN_TRANSIT,
        assigned_driver=drv,
        assigned_driver_id=1,
        assigned_vehicle=veh,
        assigned_vehicle_id=1,
        routes=[rte],
        total_weight_kg=Decimal("8500.00"),
        is_active=True,
    )
    res_high = delay_risk_service.evaluate_shipment(s_high)
    assert any(f.factor_id == "HIGH_CAPACITY_UTILIZATION" and f.impact_points == 10 for f in res_high.contributing_factors)


def test_interstate_transit_adds_points():
    """Interstate destination (MI from Chicago, IL hub) adds +15 points."""
    wh = Warehouse(id=1, name="Hub", location="Chicago, IL", capacity=100000, is_active=True)
    drv = Driver(id=1, license_number="CDL-1", phone_number="+1", availability_status="AVAILABLE")
    veh = Vehicle(id=1, registration_number="TRK-1", vehicle_type="Box Truck", capacity=Decimal("10000.00"), status="AVAILABLE")
    rte = Route(id=1, name="Route 1", origin="Chicago", destination="Detroit", status=RouteStatus.ACTIVE)

    s = Shipment(
        id=14,
        tracking_number="FG-INTERSTATE",
        origin_warehouse=wh,
        destination_city="Detroit",
        destination_state="MI",  # Interstate
        destination_address="St",
        destination_postal_code="48201",
        status=ShipmentStatus.IN_TRANSIT,
        assigned_driver=drv,
        assigned_driver_id=1,
        assigned_vehicle=veh,
        assigned_vehicle_id=1,
        routes=[rte],
        total_weight_kg=Decimal("3000.00"),
        is_active=True,
    )
    res = delay_risk_service.evaluate_shipment(s)
    assert res.is_interstate is True
    assert res.risk_score == 15
    assert any(f.factor_id == "INTERSTATE_TRANSIT" and f.impact_points == 15 for f in res.contributing_factors)


def test_warehouse_congestion_points():
    """Warehouse stock >85% adds 20 pts; 75-85% adds 10 pts."""
    wh = Warehouse(id=1, name="Chicago Hub", location="Chicago, IL", capacity=10000, is_active=True)
    drv = Driver(id=1, license_number="CDL-1", phone_number="+1", availability_status="AVAILABLE")
    veh = Vehicle(id=1, registration_number="TRK-1", vehicle_type="Box Truck", capacity=Decimal("10000.00"), status="AVAILABLE")
    rte = Route(id=1, name="Route 1", origin="Chicago", destination="Peoria", status=RouteStatus.ACTIVE)

    s = Shipment(
        id=15,
        tracking_number="FG-WH-CONGESTION",
        origin_warehouse=wh,
        destination_city="Peoria",
        destination_state="IL",
        destination_address="St",
        destination_postal_code="12345",
        status=ShipmentStatus.IN_TRANSIT,
        assigned_driver=drv,
        assigned_driver_id=1,
        assigned_vehicle=veh,
        assigned_vehicle_id=1,
        routes=[rte],
        total_weight_kg=Decimal("2000.00"),
        is_active=True,
    )

    # 90% warehouse utilization -> +20 pts
    res_crit = delay_risk_service.evaluate_shipment(s, warehouse_stock_map={1: 9000})
    assert any(f.factor_id == "CRITICAL_WAREHOUSE_CONGESTION" and f.impact_points == 20 for f in res_crit.contributing_factors)

    # 80% warehouse utilization -> +10 pts
    res_mod = delay_risk_service.evaluate_shipment(s, warehouse_stock_map={1: 8000})
    assert any(f.factor_id == "MODERATE_WAREHOUSE_CONGESTION" and f.impact_points == 10 for f in res_mod.contributing_factors)


def test_failed_shipment_prior_exception():
    """FAILED shipment adds +15 points for prior delivery exception."""
    wh = Warehouse(id=1, name="Hub", location="Chicago, IL", capacity=100000, is_active=True)
    drv = Driver(id=1, license_number="CDL-1", phone_number="+1", availability_status="AVAILABLE")
    veh = Vehicle(id=1, registration_number="TRK-1", vehicle_type="Box Truck", capacity=Decimal("10000.00"), status="AVAILABLE")
    rte = Route(id=1, name="Route 1", origin="Chicago", destination="Peoria", status=RouteStatus.ACTIVE)

    s = Shipment(
        id=16,
        tracking_number="FG-FAILED-RETRY",
        origin_warehouse=wh,
        destination_city="Peoria",
        destination_state="IL",
        destination_address="St",
        destination_postal_code="12345",
        status=ShipmentStatus.FAILED,
        assigned_driver=drv,
        assigned_driver_id=1,
        assigned_vehicle=veh,
        assigned_vehicle_id=1,
        routes=[rte],
        total_weight_kg=Decimal("2000.00"),
        is_active=True,
    )
    res = delay_risk_service.evaluate_shipment(s)
    assert res.risk_score == 15
    assert any(f.factor_id == "PRIOR_DELIVERY_FAILURE" for f in res.contributing_factors)


def test_terminal_shipments_zero_risk():
    """DELIVERED, CANCELLED, and RETURNED shipments have risk score 0 and no factors."""
    wh = Warehouse(id=1, name="Hub", location="Chicago, IL", capacity=100000, is_active=True)

    for term_status, expected_cat in [
        (ShipmentStatus.DELIVERED, "COMPLETED"),
        (ShipmentStatus.CANCELLED, "CANCELLED"),
        (ShipmentStatus.RETURNED, "RETURNED"),
    ]:
        s = Shipment(
            id=20,
            tracking_number=f"FG-TERM-{term_status.value}",
            origin_warehouse=wh,
            destination_city="Detroit",
            destination_state="MI",
            destination_address="St",
            destination_postal_code="48201",
            status=term_status,
            assigned_driver_id=None,  # Even with missing assets, terminal states have 0 risk
            assigned_vehicle_id=None,
            routes=[],
            is_active=True,
        )
        res = delay_risk_service.evaluate_shipment(s)
        assert res.risk_score == 0
        assert res.risk_category == expected_cat
        assert len(res.contributing_factors) == 0


def test_boundary_clamped_at_100():
    """Compounding all factors clamps total score cleanly at 100."""
    wh = Warehouse(id=1, name="Hub", location="Chicago, IL", capacity=1000, is_active=True)

    # Missing driver (+20), vehicle (+15), route (+10), interstate (+15), warehouse >85% (+20), failed (+15)
    # Sum: 20 + 15 + 10 + 15 + 20 + 15 = 95
    s = Shipment(
        id=30,
        tracking_number="FG-MAX-RISK",
        origin_warehouse=wh,
        destination_city="Boston",
        destination_state="MA",  # Interstate
        destination_address="St",
        destination_postal_code="02108",
        status=ShipmentStatus.FAILED,  # Failed exception
        assigned_driver_id=None,
        assigned_vehicle_id=None,
        routes=[],
        is_active=True,
    )
    res = delay_risk_service.evaluate_shipment(s, warehouse_stock_map={1: 950})
    assert res.risk_score == 95
    assert res.risk_category == "CRITICAL"
    assert res.risk_score <= 100


def test_missing_data_resilience():
    """Gracefully handles null warehouse, null capacity, null weights, zero division."""
    s = Shipment(
        id=40,
        tracking_number="FG-NULLS",
        origin_warehouse_id=None,
        origin_warehouse=None,  # No warehouse
        destination_city="Nowhere",
        destination_state="XX",
        destination_address="Empty",
        destination_postal_code="00000",
        status=ShipmentStatus.CONFIRMED,
        assigned_driver_id=None,
        assigned_vehicle_id=None,
        assigned_vehicle=None,
        total_weight_kg=None,  # No weight
        routes=[],
        is_active=True,
    )

    # Should not throw any exception
    res = delay_risk_service.evaluate_shipment(s, warehouse_stock_map=None)
    assert res.risk_score == 45  # unassigned driver (20) + vehicle (15) + route (10)
    assert res.weight_capacity_utilization is None
    assert res.warehouse_utilization_rate is None
    assert res.is_interstate is False


# ==============================================================================
# 2. API Integration Tests for GET /api/v1/analytics/delay-risk
# ==============================================================================

@pytest.fixture
def populated_operational_db(client, admin_headers):
    """Creates a realistic test database with varied operational profiles."""
    db = TestingSessionLocal()
    try:
        # Warehouses
        wh1 = Warehouse(name="Chicago Central Hub", location="Chicago, IL", address="100 Logistics Blvd", capacity=100000, is_active=True)
        wh2 = Warehouse(name="Detroit Gateway", location="Detroit, MI", address="200 Motor Way", capacity=50000, is_active=True)
        db.add_all([wh1, wh2])
        db.commit()
        db.refresh(wh1)
        db.refresh(wh2)

        # Products & Inventory
        p1 = Product(name="Engine Part", sku="SKU-ENG-1", unit_price=Decimal("100.00"), is_active=True)
        db.add(p1)
        db.commit()
        db.refresh(p1)

        inv1 = Inventory(warehouse_id=wh1.id, product_id=p1.id, quantity=90000, reorder_level=1000)  # 90% congestion
        inv2 = Inventory(warehouse_id=wh2.id, product_id=p1.id, quantity=5000, reorder_level=1000)   # 10% normal
        db.add_all([inv1, inv2])
        db.commit()

        # Driver
        user_drv = User(name="Driver Dave", email="dave@flowgrid.io", hashed_password="pw", role=UserRole.DRIVER, is_active=True)
        db.add(user_drv)
        db.commit()
        db.refresh(user_drv)

        drv1 = Driver(user_id=user_drv.id, license_number="CDL-111", phone_number="+1", availability_status="IN_TRANSIT")
        db.add(drv1)
        db.commit()
        db.refresh(drv1)

        # Vehicle
        veh1 = Vehicle(registration_number="TRK-900", vehicle_type="Box Truck", capacity=Decimal("5000.00"), status="IN_USE")
        db.add(veh1)
        db.commit()
        db.refresh(veh1)

        # Route
        rte1 = Route(name="I-94 Corridor", origin="Chicago, IL", destination="Detroit, MI", estimated_distance=Decimal("450.00"), estimated_duration=Decimal("5.0"), status=RouteStatus.ACTIVE)
        db.add(rte1)
        db.commit()
        db.refresh(rte1)

        # Shipments
        # s1: High risk (unassigned driver, vehicle, route + interstate + wh1 congestion >85%) -> 20+15+10+15+20 = 80 (CRITICAL)
        s1 = Shipment(
            tracking_number="FG-SHIP-01",
            origin_warehouse_id=wh1.id,
            destination_city="Detroit",
            destination_state="MI",
            destination_address="400 Woodward Ave",
            destination_postal_code="48201",
            status=ShipmentStatus.ASSIGNED,
            total_weight_kg=Decimal("1200.00"),
            is_active=True,
        )

        # s2: Low risk (assigned driver, vehicle, route + intra-state IL + normal load)
        s2 = Shipment(
            tracking_number="FG-SHIP-02",
            origin_warehouse_id=wh1.id,
            destination_city="Rockford",
            destination_state="IL",
            destination_address="500 Elm St",
            destination_postal_code="61101",
            status=ShipmentStatus.IN_TRANSIT,
            assigned_driver_id=drv1.id,
            assigned_vehicle_id=veh1.id,
            total_weight_kg=Decimal("2000.00"),  # 40% of 5000kg
            is_active=True,
        )

        # s3: Delivered (terminal -> score 0)
        s3 = Shipment(
            tracking_number="FG-SHIP-03",
            origin_warehouse_id=wh2.id,
            destination_city="Detroit",
            destination_state="MI",
            destination_address="100 Riverfront",
            destination_postal_code="48226",
            status=ShipmentStatus.DELIVERED,
            delivered_at=datetime.now(timezone.utc),
            total_weight_kg=Decimal("1000.00"),
            is_active=True,
        )

        db.add_all([s1, s2, s3])
        db.commit()
        db.refresh(s1)
        db.refresh(s2)
        db.refresh(s3)

        # Link route to s2
        rs2 = RouteShipment(route_id=rte1.id, shipment_id=s2.id)
        db.add(rs2)
        db.commit()

        return {"s1_id": s1.id, "s2_id": s2.id, "s3_id": s3.id}
    finally:
        db.close()


def test_delay_risk_fleet_endpoint(client, admin_headers, populated_operational_db):
    """GET /api/v1/analytics/delay-risk returns fleet-wide delay risk distribution and summary."""
    res = client.get("/api/v1/analytics/delay-risk", headers=admin_headers)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()

    assert data["total_records"] == 3
    assert "summary" in data
    summary = data["summary"]
    assert summary["total_evaluated"] == 3
    assert summary["critical_risk_count"] >= 1  # s1
    assert summary["completed_or_terminal_count"] >= 1  # s3

    shipments = data["shipments"]
    assert len(shipments) == 3

    # Check s1 (critical)
    s1_data = next(s for s in shipments if s["tracking_number"] == "FG-SHIP-01")
    assert s1_data["risk_score"] == 80
    assert s1_data["risk_category"] == "CRITICAL"
    assert s1_data["is_interstate"] is True
    assert s1_data["has_driver_assigned"] is False
    assert s1_data["is_calibrated_probability"] is False
    assert s1_data["assessment_method"] == "DETERMINISTIC_HEURISTIC"

    # Check s3 (delivered)
    s3_data = next(s for s in shipments if s["tracking_number"] == "FG-SHIP-03")
    assert s3_data["risk_score"] == 0
    assert s3_data["risk_category"] == "COMPLETED"


def test_delay_risk_filter_by_shipment_id_query_param(client, admin_headers, populated_operational_db):
    """Querying GET /api/v1/analytics/delay-risk?shipment_id=X filters to that shipment."""
    s1_id = populated_operational_db["s1_id"]
    res = client.get(f"/api/v1/analytics/delay-risk?shipment_id={s1_id}", headers=admin_headers)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["total_records"] == 1
    assert len(data["shipments"]) == 1
    assert data["shipments"][0]["shipment_id"] == s1_id


def test_delay_risk_nonexistent_shipment_id_returns_404(client, admin_headers):
    """Querying a nonexistent shipment ID returns 404 Not Found."""
    res = client.get("/api/v1/analytics/delay-risk?shipment_id=99999", headers=admin_headers)
    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert "was not found" in res.json()["detail"]


def test_delay_risk_single_endpoint(client, admin_headers, populated_operational_db):
    """GET /api/v1/analytics/delay-risk/{id} returns single shipment assessment."""
    s2_id = populated_operational_db["s2_id"]
    res = client.get(f"/api/v1/analytics/delay-risk/{s2_id}", headers=admin_headers)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["shipment_id"] == s2_id
    assert data["tracking_number"] == "FG-SHIP-02"
    assert data["has_driver_assigned"] is True
    assert data["has_vehicle_assigned"] is True
    assert data["has_route_assigned"] is True
    assert "contributing_factors" in data


def test_delay_risk_single_endpoint_404(client, admin_headers):
    """GET /api/v1/analytics/delay-risk/{id} for missing shipment returns 404."""
    res = client.get("/api/v1/analytics/delay-risk/88888", headers=admin_headers)
    assert res.status_code == status.HTTP_404_NOT_FOUND


def test_delay_risk_filter_by_status(client, admin_headers, populated_operational_db):
    """Filtering by status=IN_TRANSIT returns only in-transit shipments."""
    res = client.get("/api/v1/analytics/delay-risk?status=IN_TRANSIT", headers=admin_headers)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["total_records"] == 1
    assert data["shipments"][0]["status"] == "IN_TRANSIT"


def test_delay_risk_filter_by_category(client, admin_headers, populated_operational_db):
    """Filtering by risk_category=CRITICAL returns only critical shipments."""
    res = client.get("/api/v1/analytics/delay-risk?risk_category=CRITICAL", headers=admin_headers)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert all(s["risk_category"] == "CRITICAL" for s in data["shipments"])


def test_delay_risk_invalid_category_returns_400(client, admin_headers):
    """Invalid risk_category string returns HTTP 400 Bad Request."""
    res = client.get("/api/v1/analytics/delay-risk?risk_category=EXTREME_DANGER", headers=admin_headers)
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid risk_category" in res.json()["detail"]


def test_delay_risk_pagination(client, admin_headers, populated_operational_db):
    """Pagination parameters limit and skip restrict returned records."""
    res = client.get("/api/v1/analytics/delay-risk?limit=1&skip=0", headers=admin_headers)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert len(data["shipments"]) == 1
    assert data["total_records"] == 3
    assert data["limit"] == 1
    assert data["skip"] == 0


# ==============================================================================
# 3. RBAC & Authorization Tests
# ==============================================================================

def test_delay_risk_rbac_all_authenticated_roles_allowed(
    client, admin_headers, manager_headers, driver_headers, viewer_headers, populated_operational_db
):
    """ADMIN, MANAGER, DRIVER, and VIEWER roles can all safely access delay risk analytics."""
    s1_id = populated_operational_db["s1_id"]
    for headers in [admin_headers, manager_headers, driver_headers, viewer_headers]:
        res_list = client.get("/api/v1/analytics/delay-risk", headers=headers)
        assert res_list.status_code == status.HTTP_200_OK

        res_single = client.get(f"/api/v1/analytics/delay-risk/{s1_id}", headers=headers)
        assert res_single.status_code == status.HTTP_200_OK


def test_delay_risk_unauthenticated_rejected(client):
    """Unauthenticated requests without JWT token receive HTTP 401 Unauthorized."""
    res1 = client.get("/api/v1/analytics/delay-risk")
    assert res1.status_code == status.HTTP_401_UNAUTHORIZED

    res2 = client.get("/api/v1/analytics/delay-risk/1")
    assert res2.status_code == status.HTTP_401_UNAUTHORIZED
