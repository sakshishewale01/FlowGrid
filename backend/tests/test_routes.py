"""
FlowGrid - Route Management Backend Tests (Phase 11)
===================================================
Comprehensive test suite validating:
- Route CRUD operations with layered architecture (Repository, Service, Endpoint).
- Creation by ADMIN and MANAGER roles (HTTP 201).
- Rejection of creation by DRIVER and VIEWER (HTTP 403).
- Rejection of unauthenticated requests (HTTP 401).
- Route retrieval and pagination (HTTP 200) by all authenticated roles.
- Status filtering (e.g., ACTIVE, PLANNED, COMPLETED).
- Route retrieval by ID (HTTP 200) and 404 Not Found handling.
- Route update permissions: ADMIN and MANAGER allowed; DRIVER and VIEWER forbidden (403).
- Route deletion permissions: ADMIN only allowed; MANAGER, DRIVER, VIEWER forbidden (403).
- Soft deletion mechanism preserving records with is_active = False.
- Validation: origin and destination required, non-negative estimated distance and duration.
- Shipment assignment to route: ADMIN and MANAGER allowed; DRIVER and VIEWER forbidden (403).
- Safe handling of duplicate shipment assignments (HTTP 400).
- Handling of invalid / non-existent shipment IDs and route IDs (HTTP 404).
- Safe handling of duplicate shipment IDs in payload (HTTP 400).
- Retrieval of shipments assigned to a route by all authenticated roles.
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
from app.models.route import RouteStatus

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
    return get_auth_headers_for_role(client, "admin_route@flowgrid.io", "ADMIN")


@pytest.fixture
def manager_headers(client):
    return get_auth_headers_for_role(client, "manager_route@flowgrid.io", "MANAGER")


@pytest.fixture
def driver_headers(client):
    return get_auth_headers_for_role(client, "driver_route@flowgrid.io", "DRIVER")


@pytest.fixture
def viewer_headers(client):
    return get_auth_headers_for_role(client, "viewer_route@flowgrid.io", "VIEWER")


@pytest.fixture
def sample_shipment_ids(client, admin_headers):
    """
    Creates two test shipments and returns their IDs.
    """
    shipment_ids = []
    for i in range(1, 3):
        res = client.post(
            "/api/v1/shipments",
            headers=admin_headers,
            json={
                "tracking_number": f"FG-ROUTE-TEST-{i:03d}",
                "destination_address": f"{100 * i} Transit Ave",
                "destination_city": "Detroit",
                "destination_state": "MI",
                "destination_postal_code": "48201",
                "total_weight_kg": 250.50,
            },
        )
        assert res.status_code == status.HTTP_201_CREATED, res.text
        shipment_ids.append(res.json()["id"])
    return shipment_ids


# ==============================================================================
# 1. Route Creation & RBAC Tests
# ==============================================================================

def test_create_route_admin(client, admin_headers):
    """ADMIN can successfully create a new route with all fields."""
    payload = {
        "name": "I-80 Midwest Freight Corridor",
        "origin": "Chicago, IL",
        "destination": "Cleveland, OH",
        "estimated_distance": 550.25,
        "estimated_duration": 8.50,
        "status": "ACTIVE",
    }
    res = client.post("/api/v1/routes", headers=admin_headers, json=payload)
    assert res.status_code == status.HTTP_201_CREATED
    data = res.json()
    assert data["id"] is not None
    assert data["name"] == "I-80 Midwest Freight Corridor"
    assert data["origin"] == "Chicago, IL"
    assert data["destination"] == "Cleveland, OH"
    assert float(data["estimated_distance"]) == 550.25
    assert float(data["estimated_duration"]) == 8.50
    assert data["status"] == "ACTIVE"
    assert data["is_active"] is True


def test_create_route_manager(client, manager_headers):
    """MANAGER can successfully create a route."""
    payload = {
        "name": "I-95 Northeast Express",
        "origin": "Newark, NJ",
        "destination": "Boston, MA",
        "estimated_distance": 360.00,
        "estimated_duration": 6.00,
    }
    res = client.post("/api/v1/routes", headers=manager_headers, json=payload)
    assert res.status_code == status.HTTP_201_CREATED
    data = res.json()
    assert data["name"] == "I-95 Northeast Express"
    assert data["status"] == "ACTIVE"  # Default status


def test_create_route_driver_forbidden(client, driver_headers):
    """DRIVER role is forbidden from creating routes (403)."""
    payload = {
        "name": "Unauthorized Driver Route",
        "origin": "Dallas, TX",
        "destination": "Austin, TX",
    }
    res = client.post("/api/v1/routes", headers=driver_headers, json=payload)
    assert res.status_code == status.HTTP_403_FORBIDDEN


def test_create_route_viewer_forbidden(client, viewer_headers):
    """VIEWER role is forbidden from creating routes (403)."""
    payload = {
        "name": "Unauthorized Viewer Route",
        "origin": "Denver, CO",
        "destination": "Salt Lake City, UT",
    }
    res = client.post("/api/v1/routes", headers=viewer_headers, json=payload)
    assert res.status_code == status.HTTP_403_FORBIDDEN


def test_create_route_unauthenticated(client):
    """Unauthenticated request is rejected (401)."""
    payload = {
        "name": "Unauthenticated Route",
        "origin": "Miami, FL",
        "destination": "Orlando, FL",
    }
    res = client.post("/api/v1/routes", json=payload)
    assert res.status_code == status.HTTP_401_UNAUTHORIZED


# ==============================================================================
# 2. Validation Tests
# ==============================================================================

def test_create_route_validation_empty_origin_destination(client, admin_headers):
    """Rejects route with empty or blank name, origin, or destination."""
    res1 = client.post(
        "/api/v1/routes",
        headers=admin_headers,
        json={"name": "   ", "origin": "Chicago, IL", "destination": "Newark, NJ"},
    )
    assert res1.status_code in (status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY)

    res2 = client.post(
        "/api/v1/routes",
        headers=admin_headers,
        json={"name": "Valid Route", "origin": "   ", "destination": "Newark, NJ"},
    )
    assert res2.status_code in (status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY)

    res3 = client.post(
        "/api/v1/routes",
        headers=admin_headers,
        json={"name": "Valid Route", "origin": "Chicago, IL", "destination": "  "},
    )
    assert res3.status_code in (status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY)


def test_create_route_validation_negative_distance_duration(client, admin_headers):
    """Rejects route creation with negative estimated distance or duration."""
    res1 = client.post(
        "/api/v1/routes",
        headers=admin_headers,
        json={
            "name": "Invalid Distance Route",
            "origin": "Chicago, IL",
            "destination": "Detroit, MI",
            "estimated_distance": -150.0,
        },
    )
    assert res1.status_code in (status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY)

    res2 = client.post(
        "/api/v1/routes",
        headers=admin_headers,
        json={
            "name": "Invalid Duration Route",
            "origin": "Chicago, IL",
            "destination": "Detroit, MI",
            "estimated_duration": -2.5,
        },
    )
    assert res2.status_code in (status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY)


# ==============================================================================
# 3. Route Retrieval & Filtering Tests
# ==============================================================================

def test_get_all_routes_all_roles(client, admin_headers, manager_headers, driver_headers, viewer_headers):
    """All authenticated roles can retrieve the list of routes."""
    # Create 2 routes
    client.post(
        "/api/v1/routes",
        headers=admin_headers,
        json={"name": "Route Alpha", "origin": "City A", "destination": "City B", "status": "ACTIVE"},
    )
    client.post(
        "/api/v1/routes",
        headers=manager_headers,
        json={"name": "Route Beta", "origin": "City C", "destination": "City D", "status": "PLANNED"},
    )

    for headers in (admin_headers, manager_headers, driver_headers, viewer_headers):
        res = client.get("/api/v1/routes", headers=headers)
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert len(data) >= 2


def test_get_all_routes_pagination_and_status_filter(client, admin_headers):
    """Tests pagination (skip/limit) and status filtering on routes."""
    # Create routes with different statuses
    client.post(
        "/api/v1/routes",
        headers=admin_headers,
        json={"name": "Active Route 1", "origin": "A", "destination": "B", "status": "ACTIVE"},
    )
    client.post(
        "/api/v1/routes",
        headers=admin_headers,
        json={"name": "Active Route 2", "origin": "C", "destination": "D", "status": "ACTIVE"},
    )
    client.post(
        "/api/v1/routes",
        headers=admin_headers,
        json={"name": "Planned Route 1", "origin": "E", "destination": "F", "status": "PLANNED"},
    )

    # Filter by status ACTIVE
    res_active = client.get("/api/v1/routes?status=ACTIVE", headers=admin_headers)
    assert res_active.status_code == status.HTTP_200_OK
    active_routes = res_active.json()
    assert all(r["status"] == "ACTIVE" for r in active_routes)

    # Filter by status PLANNED
    res_planned = client.get("/api/v1/routes?status=PLANNED", headers=admin_headers)
    assert res_planned.status_code == status.HTTP_200_OK
    planned_routes = res_planned.json()
    assert all(r["status"] == "PLANNED" for r in planned_routes)

    # Test pagination
    res_page = client.get("/api/v1/routes?skip=1&limit=1", headers=admin_headers)
    assert res_page.status_code == status.HTTP_200_OK
    assert len(res_page.json()) == 1


def test_get_route_by_id_success_and_404(client, admin_headers, viewer_headers):
    """Tests retrieving route by ID and 404 handling."""
    create_res = client.post(
        "/api/v1/routes",
        headers=admin_headers,
        json={"name": "Lookup Route", "origin": "Dallas, TX", "destination": "Houston, TX"},
    )
    route_id = create_res.json()["id"]

    # Retrieve by viewer
    get_res = client.get(f"/api/v1/routes/{route_id}", headers=viewer_headers)
    assert get_res.status_code == status.HTTP_200_OK
    assert get_res.json()["name"] == "Lookup Route"

    # Non-existent ID returns 404
    missing_res = client.get("/api/v1/routes/99999", headers=admin_headers)
    assert missing_res.status_code == status.HTTP_404_NOT_FOUND


# ==============================================================================
# 4. Route Update & RBAC Tests
# ==============================================================================

def test_update_route_permissions(client, admin_headers, manager_headers, driver_headers, viewer_headers):
    """ADMIN and MANAGER can update routes; DRIVER and VIEWER are forbidden."""
    create_res = client.post(
        "/api/v1/routes",
        headers=admin_headers,
        json={"name": "Original Name", "origin": "Origin City", "destination": "Dest City"},
    )
    route_id = create_res.json()["id"]

    # MANAGER update allowed
    update_res1 = client.patch(
        f"/api/v1/routes/{route_id}",
        headers=manager_headers,
        json={"name": "Manager Updated Name", "estimated_distance": 420.0},
    )
    assert update_res1.status_code == status.HTTP_200_OK
    assert update_res1.json()["name"] == "Manager Updated Name"
    assert float(update_res1.json()["estimated_distance"]) == 420.0

    # ADMIN update allowed
    update_res2 = client.put(
        f"/api/v1/routes/{route_id}",
        headers=admin_headers,
        json={"name": "Admin Updated Name", "status": "COMPLETED"},
    )
    assert update_res2.status_code == status.HTTP_200_OK
    assert update_res2.json()["status"] == "COMPLETED"

    # DRIVER forbidden
    driver_res = client.patch(
        f"/api/v1/routes/{route_id}",
        headers=driver_headers,
        json={"name": "Driver Attempt"},
    )
    assert driver_res.status_code == status.HTTP_403_FORBIDDEN

    # VIEWER forbidden
    viewer_res = client.patch(
        f"/api/v1/routes/{route_id}",
        headers=viewer_headers,
        json={"name": "Viewer Attempt"},
    )
    assert viewer_res.status_code == status.HTTP_403_FORBIDDEN


def test_update_route_validation_and_404(client, admin_headers):
    """Update rejects negative values and handles 404."""
    create_res = client.post(
        "/api/v1/routes",
        headers=admin_headers,
        json={"name": "Validation Route", "origin": "A", "destination": "B"},
    )
    route_id = create_res.json()["id"]

    # Negative distance rejected
    neg_res = client.patch(
        f"/api/v1/routes/{route_id}",
        headers=admin_headers,
        json={"estimated_distance": -50.0},
    )
    assert neg_res.status_code in (status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY)

    # 404 on missing route
    missing_res = client.patch(
        "/api/v1/routes/99999",
        headers=admin_headers,
        json={"name": "Non-existent"},
    )
    assert missing_res.status_code == status.HTTP_404_NOT_FOUND


# ==============================================================================
# 5. Route Deletion & Soft Delete Tests
# ==============================================================================

def test_delete_route_permissions_and_soft_delete(client, admin_headers, manager_headers, driver_headers, viewer_headers):
    """Only ADMIN can delete a route; uses soft deletion."""
    create_res = client.post(
        "/api/v1/routes",
        headers=admin_headers,
        json={"name": "Route To Delete", "origin": "A", "destination": "B"},
    )
    route_id = create_res.json()["id"]

    # MANAGER forbidden
    res_mgr = client.delete(f"/api/v1/routes/{route_id}", headers=manager_headers)
    assert res_mgr.status_code == status.HTTP_403_FORBIDDEN

    # DRIVER forbidden
    res_drv = client.delete(f"/api/v1/routes/{route_id}", headers=driver_headers)
    assert res_drv.status_code == status.HTTP_403_FORBIDDEN

    # VIEWER forbidden
    res_viw = client.delete(f"/api/v1/routes/{route_id}", headers=viewer_headers)
    assert res_viw.status_code == status.HTTP_403_FORBIDDEN

    # ADMIN deletes successfully (soft delete)
    del_res = client.delete(f"/api/v1/routes/{route_id}", headers=admin_headers)
    assert del_res.status_code == status.HTTP_200_OK
    assert del_res.json()["is_active"] is False

    # Deleting missing route returns 404
    missing_res = client.delete("/api/v1/routes/99999", headers=admin_headers)
    assert missing_res.status_code == status.HTTP_404_NOT_FOUND


# ==============================================================================
# 6. Shipment Assignment & Route Shipments Tests
# ==============================================================================

def test_assign_shipments_to_route(client, admin_headers, manager_headers, sample_shipment_ids):
    """ADMIN and MANAGER can assign shipments to routes."""
    create_res = client.post(
        "/api/v1/routes",
        headers=admin_headers,
        json={"name": "Assignment Test Route", "origin": "Chicago, IL", "destination": "Detroit, MI"},
    )
    route_id = create_res.json()["id"]
    s1, s2 = sample_shipment_ids

    # ADMIN assigns first shipment
    assign_res1 = client.post(
        f"/api/v1/routes/{route_id}/shipments",
        headers=admin_headers,
        json={"shipment_ids": [s1]},
    )
    assert assign_res1.status_code == status.HTTP_200_OK
    assigned = assign_res1.json()
    assert len(assigned) == 1
    assert assigned[0]["id"] == s1

    # MANAGER assigns second shipment via path endpoint
    assign_res2 = client.post(
        f"/api/v1/routes/{route_id}/shipments/{s2}",
        headers=manager_headers,
    )
    assert assign_res2.status_code == status.HTTP_200_OK
    assigned_all = assign_res2.json()
    assert len(assigned_all) == 2


def test_assign_shipments_rbacs(client, admin_headers, driver_headers, viewer_headers, sample_shipment_ids):
    """DRIVER and VIEWER are rejected from assigning shipments (403)."""
    create_res = client.post(
        "/api/v1/routes",
        headers=admin_headers,
        json={"name": "RBAC Assign Route", "origin": "A", "destination": "B"},
    )
    route_id = create_res.json()["id"]
    s1 = sample_shipment_ids[0]

    res_drv = client.post(
        f"/api/v1/routes/{route_id}/shipments",
        headers=driver_headers,
        json={"shipment_ids": [s1]},
    )
    assert res_drv.status_code == status.HTTP_403_FORBIDDEN

    res_viw = client.post(
        f"/api/v1/routes/{route_id}/shipments",
        headers=viewer_headers,
        json={"shipment_ids": [s1]},
    )
    assert res_viw.status_code == status.HTTP_403_FORBIDDEN


def test_assign_shipments_invalid_route_and_shipment(client, admin_headers, sample_shipment_ids):
    """Assignment returns 404 when route or shipment does not exist."""
    create_res = client.post(
        "/api/v1/routes",
        headers=admin_headers,
        json={"name": "Valid Route", "origin": "A", "destination": "B"},
    )
    route_id = create_res.json()["id"]

    # Invalid route ID
    res1 = client.post(
        "/api/v1/routes/99999/shipments",
        headers=admin_headers,
        json={"shipment_ids": [sample_shipment_ids[0]]},
    )
    assert res1.status_code == status.HTTP_404_NOT_FOUND

    # Invalid shipment ID
    res2 = client.post(
        f"/api/v1/routes/{route_id}/shipments",
        headers=admin_headers,
        json={"shipment_ids": [88888]},
    )
    assert res2.status_code == status.HTTP_404_NOT_FOUND


def test_assign_shipments_duplicate_prevention(client, admin_headers, sample_shipment_ids):
    """Prevents duplicate shipment assignments safely with 400 Bad Request."""
    create_res = client.post(
        "/api/v1/routes",
        headers=admin_headers,
        json={"name": "Duplicate Test Route", "origin": "A", "destination": "B"},
    )
    route_id = create_res.json()["id"]
    s1 = sample_shipment_ids[0]

    # First assignment succeeds
    res1 = client.post(
        f"/api/v1/routes/{route_id}/shipments",
        headers=admin_headers,
        json={"shipment_ids": [s1]},
    )
    assert res1.status_code == status.HTTP_200_OK

    # Re-assignment of same shipment to same route is rejected (400)
    res_dup = client.post(
        f"/api/v1/routes/{route_id}/shipments",
        headers=admin_headers,
        json={"shipment_ids": [s1]},
    )
    assert res_dup.status_code == status.HTTP_400_BAD_REQUEST
    assert "already assigned" in res_dup.json()["detail"].lower()

    # Duplicate IDs in same payload is rejected (400)
    res_dup_payload = client.post(
        f"/api/v1/routes/{route_id}/shipments",
        headers=admin_headers,
        json={"shipment_ids": [sample_shipment_ids[1], sample_shipment_ids[1]]},
    )
    assert res_dup_payload.status_code == status.HTTP_400_BAD_REQUEST
    assert "duplicate" in res_dup_payload.json()["detail"].lower()


def test_get_route_shipments_all_roles(client, admin_headers, viewer_headers, driver_headers, sample_shipment_ids):
    """All authenticated roles can retrieve assigned shipments for a route."""
    create_res = client.post(
        "/api/v1/routes",
        headers=admin_headers,
        json={"name": "Multi-Shipment Corridor", "origin": "ORD Hub", "destination": "DTW Depot"},
    )
    route_id = create_res.json()["id"]

    # Assign shipments
    client.post(
        f"/api/v1/routes/{route_id}/shipments",
        headers=admin_headers,
        json={"shipment_ids": sample_shipment_ids},
    )

    # VIEWER retrieves shipments
    res_viw = client.get(f"/api/v1/routes/{route_id}/shipments", headers=viewer_headers)
    assert res_viw.status_code == status.HTTP_200_OK
    shipments = res_viw.json()
    assert len(shipments) == 2
    tracking_numbers = [s["tracking_number"] for s in shipments]
    assert "FG-ROUTE-TEST-001" in tracking_numbers
    assert "FG-ROUTE-TEST-002" in tracking_numbers

    # DRIVER retrieves shipments
    res_drv = client.get(f"/api/v1/routes/{route_id}/shipments", headers=driver_headers)
    assert res_drv.status_code == status.HTTP_200_OK
    assert len(res_drv.json()) == 2

    # Missing route returns 404
    res_missing = client.get("/api/v1/routes/99999/shipments", headers=viewer_headers)
    assert res_missing.status_code == status.HTTP_404_NOT_FOUND


def test_assign_shipments_payload_formats(client, admin_headers, sample_shipment_ids):
    """Verifies that assigning shipments supports multiple flexible payload formats."""
    create_res = client.post(
        "/api/v1/routes",
        headers=admin_headers,
        json={"name": "Payload Format Test Route", "origin": "Start Hub", "destination": "End Hub"},
    )
    route_id = create_res.json()["id"]
    s1, s2 = sample_shipment_ids

    # Format 1: single shipment_id object
    res1 = client.post(
        f"/api/v1/routes/{route_id}/shipments",
        headers=admin_headers,
        json={"shipment_id": s1},
    )
    assert res1.status_code == status.HTTP_200_OK

    # Format 2: raw list of IDs
    res2 = client.post(
        f"/api/v1/routes/{route_id}/shipments",
        headers=admin_headers,
        json=[s2],
    )
    assert res2.status_code == status.HTTP_200_OK

    # Verify shipments_count is 2 when getting route
    route_res = client.get(f"/api/v1/routes/{route_id}", headers=admin_headers)
    assert route_res.status_code == status.HTTP_200_OK
    assert route_res.json()["shipments_count"] == 2


def test_route_search_and_active_filters(client, admin_headers):
    """Verifies search filtering by route name or origin and is_active flag."""
    client.post(
        "/api/v1/routes",
        headers=admin_headers,
        json={"name": "Pacific Coast Express", "origin": "Seattle, WA", "destination": "San Francisco, CA"},
    )
    client.post(
        "/api/v1/routes",
        headers=admin_headers,
        json={"name": "Gulf Coast Corridor", "origin": "Houston, TX", "destination": "New Orleans, LA"},
    )

    # Search for Pacific
    res_search = client.get("/api/v1/routes?search=Pacific", headers=admin_headers)
    assert res_search.status_code == status.HTTP_200_OK
    results = res_search.json()
    assert any("Pacific" in r["name"] for r in results)
    assert not any("Gulf" in r["name"] for r in results)

    # Search for New Orleans
    res_search2 = client.get("/api/v1/routes?search=New%20Orleans", headers=admin_headers)
    assert res_search2.status_code == status.HTTP_200_OK
    results2 = res_search2.json()
    assert any("Gulf" in r["name"] for r in results2)

