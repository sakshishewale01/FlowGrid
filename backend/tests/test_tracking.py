"""
FlowGrid - Shipment Tracking and Status History Tests
=====================================================
Comprehensive test suite validating:
- Automatic status history record creation on shipment registration.
- Atomicity and persistence of status transition history with remarks and user attribution.
- Prevention of duplicate status history records upon idempotent calls.
- Rejection of invalid status transitions without history pollution.
- Chronological ordering (newest to oldest) and pagination of status history.
- Granular tracking events (checkpoints, scans) creation by ADMIN and MANAGER.
- RBAC enforcement: DRIVER and VIEWER forbidden from adding tracking events (403).
- Tracking history retrieval by all authenticated roles.
- Aggregated latest tracking information endpoint.
- 404 Not Found handling for nonexistent shipments across all endpoints.
- Transaction rollback safety.
"""

from datetime import datetime, timezone
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import patch

from app.api.deps import get_db
from app.db.base import Base
from app.main import app
from app.models.shipment import ShipmentStatus
from app.services.shipment_service import shipment_service
from app.schemas.shipment import ShipmentStatusUpdate

# ------------------------------------------------------------------------------
# In-Memory SQLite Test Engine & DB Setup
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
    return get_auth_headers_for_role(client, "admin_track@flowgrid.io", "ADMIN")


@pytest.fixture
def manager_headers(client):
    return get_auth_headers_for_role(client, "manager_track@flowgrid.io", "MANAGER")


@pytest.fixture
def driver_headers(client):
    return get_auth_headers_for_role(client, "driver_track@flowgrid.io", "DRIVER")


@pytest.fixture
def viewer_headers(client):
    return get_auth_headers_for_role(client, "viewer_track@flowgrid.io", "VIEWER")


@pytest.fixture
def sample_shipment(client, admin_headers):
    payload = {
        "destination_address": "1200 Logistics Blvd",
        "destination_city": "Chicago",
        "destination_state": "IL",
        "destination_postal_code": "60601",
        "total_weight_kg": 250.00,
        "total_volume_cbm": 1.75,
    }
    res = client.post("/api/v1/shipments", json=payload, headers=admin_headers)
    assert res.status_code == status.HTTP_201_CREATED
    return res.json()


# ------------------------------------------------------------------------------
# 1. Status History Tests
# ------------------------------------------------------------------------------

def test_automatic_status_history_creation_on_shipment_create(client, admin_headers, sample_shipment):
    """
    Creating a shipment must automatically create an initial status history record with status CREATED.
    """
    shipment_id = sample_shipment["id"]

    res = client.get(f"/api/v1/shipments/{shipment_id}/history", headers=admin_headers)
    assert res.status_code == status.HTTP_200_OK
    history = res.json()
    assert len(history) == 1
    assert history[0]["previous_status"] is None
    assert history[0]["new_status"] == ShipmentStatus.CREATED
    assert history[0]["remarks"] == "Shipment registered"
    assert history[0]["changed_by"] is not None
    assert history[0]["changed_by"]["email"] == "admin_track@flowgrid.io"


def test_status_transition_creates_history_record_with_remarks(client, admin_headers, manager_headers, sample_shipment):
    """
    Valid status transition appends a history record with previous/new status and remarks.
    """
    shipment_id = sample_shipment["id"]

    # Transition CREATED -> CONFIRMED via Manager
    res = client.patch(
        f"/api/v1/shipments/{shipment_id}/status",
        json={"status": "CONFIRMED", "remarks": "Confirmed by warehouse dispatch supervisor"},
        headers=manager_headers,
    )
    assert res.status_code == status.HTTP_200_OK

    # Verify history
    hist_res = client.get(f"/api/v1/shipments/{shipment_id}/history", headers=admin_headers)
    assert hist_res.status_code == status.HTTP_200_OK
    history = hist_res.json()
    assert len(history) == 2

    # Ordered newest first
    newest = history[0]
    oldest = history[1]

    assert newest["previous_status"] == ShipmentStatus.CREATED
    assert newest["new_status"] == ShipmentStatus.CONFIRMED
    assert newest["remarks"] == "Confirmed by warehouse dispatch supervisor"
    assert newest["changed_by"]["email"] == "manager_track@flowgrid.io"

    assert oldest["previous_status"] is None
    assert oldest["new_status"] == ShipmentStatus.CREATED


def test_duplicate_status_update_avoids_duplicate_history(client, admin_headers, sample_shipment):
    """
    Calling update status with the current status should be idempotent and not create duplicate history.
    """
    shipment_id = sample_shipment["id"]

    # Confirm once
    client.patch(
        f"/api/v1/shipments/{shipment_id}/status",
        json={"status": "CONFIRMED", "remarks": "First confirmation"},
        headers=admin_headers,
    )

    # Attempt to confirm again with identical status
    res = client.patch(
        f"/api/v1/shipments/{shipment_id}/status",
        json={"status": "CONFIRMED", "remarks": "Duplicate call"},
        headers=admin_headers,
    )
    assert res.status_code == status.HTTP_200_OK

    # History count should still be 2 (initial CREATED + first CONFIRMED)
    hist_res = client.get(f"/api/v1/shipments/{shipment_id}/history", headers=admin_headers)
    assert len(hist_res.json()) == 2


def test_invalid_status_transition_does_not_create_history(client, admin_headers, sample_shipment):
    """
    An invalid status transition must return 400 and create no history record.
    """
    shipment_id = sample_shipment["id"]

    # Illegal jump: CREATED -> DELIVERED
    res = client.patch(
        f"/api/v1/shipments/{shipment_id}/status",
        json={"status": "DELIVERED"},
        headers=admin_headers,
    )
    assert res.status_code == status.HTTP_400_BAD_REQUEST

    hist_res = client.get(f"/api/v1/shipments/{shipment_id}/history", headers=admin_headers)
    assert len(hist_res.json()) == 1  # Only initial CREATED


def test_status_history_ordering_and_pagination(client, admin_headers, sample_shipment):
    """
    Tests multiple status changes and pagination ordering.
    """
    shipment_id = sample_shipment["id"]

    transitions = [
        ("CONFIRMED", "Dispatch confirmed"),
        ("ASSIGNED", "Assigned to driver"),
        ("PICKED_UP", "Cargo loaded into truck"),
    ]
    for target, remark in transitions:
        res = client.patch(
            f"/api/v1/shipments/{shipment_id}/status",
            json={"status": target, "remarks": remark},
            headers=admin_headers,
        )
        assert res.status_code == status.HTTP_200_OK

    # Total 4 records (CREATED, CONFIRMED, ASSIGNED, PICKED_UP)
    # Page 1: limit 2
    res_page1 = client.get(
        f"/api/v1/shipments/{shipment_id}/history?skip=0&limit=2",
        headers=admin_headers,
    )
    assert res_page1.status_code == status.HTTP_200_OK
    items_p1 = res_page1.json()
    assert len(items_p1) == 2
    assert items_p1[0]["new_status"] == ShipmentStatus.PICKED_UP
    assert items_p1[1]["new_status"] == ShipmentStatus.ASSIGNED

    # Page 2: skip 2, limit 2
    res_page2 = client.get(
        f"/api/v1/shipments/{shipment_id}/history?skip=2&limit=2",
        headers=admin_headers,
    )
    items_p2 = res_page2.json()
    assert len(items_p2) == 2
    assert items_p2[0]["new_status"] == ShipmentStatus.CONFIRMED
    assert items_p2[1]["new_status"] == ShipmentStatus.CREATED


def test_get_history_missing_shipment_returns_404(client, admin_headers):
    """
    Querying status history for nonexistent shipment returns 404.
    """
    res = client.get("/api/v1/shipments/99999/history", headers=admin_headers)
    assert res.status_code == status.HTTP_404_NOT_FOUND


def test_get_history_accessible_to_all_authenticated_roles(client, admin_headers, driver_headers, viewer_headers, sample_shipment):
    """
    All authenticated roles (DRIVER, VIEWER) can read status history.
    """
    shipment_id = sample_shipment["id"]

    for headers in [driver_headers, viewer_headers]:
        res = client.get(f"/api/v1/shipments/{shipment_id}/history", headers=headers)
        assert res.status_code == status.HTTP_200_OK
        assert len(res.json()) >= 1


# ------------------------------------------------------------------------------
# 2. Tracking Events Tests
# ------------------------------------------------------------------------------

def test_add_tracking_event_as_admin_and_manager(client, admin_headers, manager_headers, sample_shipment):
    """
    ADMIN and MANAGER can record physical tracking events.
    """
    shipment_id = sample_shipment["id"]

    # Admin records CHECKPOINT
    admin_payload = {
        "event_type": "CHECKPOINT",
        "location": "Regional Hub A, Chicago, IL",
        "description": "Package received at automated sorter",
    }
    admin_res = client.post(
        f"/api/v1/shipments/{shipment_id}/tracking",
        json=admin_payload,
        headers=admin_headers,
    )
    assert admin_res.status_code == status.HTTP_201_CREATED
    data = admin_res.json()
    assert data["event_type"] == "CHECKPOINT"
    assert data["location"] == "Regional Hub A, Chicago, IL"
    assert data["description"] == "Package received at automated sorter"
    assert data["created_by"]["email"] == "admin_track@flowgrid.io"

    # Manager records SCAN
    manager_payload = {
        "event_type": "SCAN",
        "location": "Outbound Dock 4, Chicago, IL",
        "description": "Loaded into cross-country container trailer",
    }
    manager_res = client.post(
        f"/api/v1/shipments/{shipment_id}/tracking",
        json=manager_payload,
        headers=manager_headers,
    )
    assert manager_res.status_code == status.HTTP_201_CREATED
    assert manager_res.json()["event_type"] == "SCAN"


def test_add_tracking_event_forbidden_for_driver_and_viewer(client, driver_headers, viewer_headers, sample_shipment):
    """
    DRIVER and VIEWER roles are forbidden from adding tracking events (403).
    """
    shipment_id = sample_shipment["id"]
    payload = {
        "event_type": "CHECKPOINT",
        "location": "Rest Stop #12, Gary, IN",
        "description": "Driver check-in",
    }

    driver_res = client.post(
        f"/api/v1/shipments/{shipment_id}/tracking",
        json=payload,
        headers=driver_headers,
    )
    assert driver_res.status_code == status.HTTP_403_FORBIDDEN

    viewer_res = client.post(
        f"/api/v1/shipments/{shipment_id}/tracking",
        json=payload,
        headers=viewer_headers,
    )
    assert viewer_res.status_code == status.HTTP_403_FORBIDDEN


def test_add_tracking_event_missing_shipment_returns_404(client, admin_headers):
    """
    Attempting to add tracking event to nonexistent shipment returns 404.
    """
    payload = {
        "event_type": "CHECKPOINT",
        "location": "Nowhere",
        "description": "No shipment exists",
    }
    res = client.post("/api/v1/shipments/99999/tracking", json=payload, headers=admin_headers)
    assert res.status_code == status.HTTP_404_NOT_FOUND


def test_get_tracking_events_ordering_and_all_roles(client, admin_headers, driver_headers, sample_shipment):
    """
    Retrieves tracking events ordered newest first. Accessible to DRIVER role.
    """
    shipment_id = sample_shipment["id"]

    # Add 2 events
    client.post(
        f"/api/v1/shipments/{shipment_id}/tracking",
        json={
            "event_type": "ARRIVED",
            "location": "Facility 1",
            "description": "Arrived at initial hub",
            "timestamp": "2026-09-19T10:00:00Z",
        },
        headers=admin_headers,
    )
    client.post(
        f"/api/v1/shipments/{shipment_id}/tracking",
        json={
            "event_type": "DEPARTED",
            "location": "Facility 1",
            "description": "Departed for transit",
            "timestamp": "2026-09-19T12:00:00Z",
        },
        headers=admin_headers,
    )

    # Query with driver headers
    res = client.get(f"/api/v1/shipments/{shipment_id}/tracking", headers=driver_headers)
    assert res.status_code == status.HTTP_200_OK
    events = res.json()
    assert len(events) == 2
    # Newest timestamp first
    assert events[0]["event_type"] == "DEPARTED"
    assert events[1]["event_type"] == "ARRIVED"


# ------------------------------------------------------------------------------
# 3. Latest Tracking Info Tests
# ------------------------------------------------------------------------------

def test_get_latest_tracking_info(client, admin_headers, viewer_headers, sample_shipment):
    """
    Tests consolidated latest tracking info endpoint.
    """
    shipment_id = sample_shipment["id"]

    # Initial view (before transitions and events)
    initial_res = client.get(
        f"/api/v1/shipments/{shipment_id}/tracking/latest",
        headers=viewer_headers,
    )
    assert initial_res.status_code == status.HTTP_200_OK
    initial_data = initial_res.json()
    assert initial_data["current_status"] == ShipmentStatus.CREATED
    assert initial_data["latest_status_history"] is not None
    assert initial_data["latest_status_history"]["new_status"] == ShipmentStatus.CREATED
    assert initial_data["latest_tracking_event"] is None

    # Advance status to CONFIRMED
    client.patch(
        f"/api/v1/shipments/{shipment_id}/status",
        json={"status": "CONFIRMED", "remarks": "Dispatch verified"},
        headers=admin_headers,
    )

    # Add tracking event
    client.post(
        f"/api/v1/shipments/{shipment_id}/tracking",
        json={
            "event_type": "SCAN",
            "location": "Dock A",
            "description": "Cargo scan complete",
        },
        headers=admin_headers,
    )

    # Re-check latest view
    updated_res = client.get(
        f"/api/v1/shipments/{shipment_id}/tracking/latest",
        headers=viewer_headers,
    )
    assert updated_res.status_code == status.HTTP_200_OK
    updated_data = updated_res.json()
    assert updated_data["current_status"] == ShipmentStatus.CONFIRMED
    assert updated_data["latest_status_history"]["new_status"] == ShipmentStatus.CONFIRMED
    assert updated_data["latest_tracking_event"]["event_type"] == "SCAN"
    assert updated_data["latest_tracking_event"]["location"] == "Dock A"


def test_get_latest_tracking_info_missing_shipment_returns_404(client, viewer_headers):
    """
    Latest tracking lookup for missing shipment returns 404.
    """
    res = client.get("/api/v1/shipments/99999/tracking/latest", headers=viewer_headers)
    assert res.status_code == status.HTTP_404_NOT_FOUND


# ------------------------------------------------------------------------------
# 4. Transaction Rollback Safety Test
# ------------------------------------------------------------------------------

def test_status_update_transaction_rollback_on_failure(sample_shipment):
    """
    Verifies that if an unhandled error occurs during the status update / history creation,
    the database transaction is rolled back and the status is not partially committed.
    """
    db = TestingSessionLocal()
    try:
        shipment_id = sample_shipment["id"]
        update_payload = ShipmentStatusUpdate(status=ShipmentStatus.CONFIRMED, remarks="Will fail")

        # Mock db.commit to simulate database constraint/disk error
        with patch.object(db, "commit", side_effect=RuntimeError("Simulated database failure")):
            with pytest.raises(RuntimeError, match="Simulated database failure"):
                shipment_service.update_shipment_status(db, shipment_id, update_payload)

        # Confirm that the status in the fresh database session was rolled back and is still CREATED
        fresh_shipment = shipment_service.get_shipment(db, shipment_id)
        assert fresh_shipment.status == ShipmentStatus.CREATED
    finally:
        db.close()
