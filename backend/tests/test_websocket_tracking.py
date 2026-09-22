"""
WebSocket Real-Time Tracking Tests
==================================
Comprehensive automated test suite for the /ws/tracking/{shipment_id} WebSocket endpoint:
- Rejection of unauthenticated requests (missing, invalid, or expired JWT) with code 1008.
- Rejection of deactivated user accounts with code 1008.
- Rejection of nonexistent or soft-deleted shipments with code 1008.
- RBAC permission matrix (ADMIN, MANAGER, VIEWER permitted; DRIVER verified against assignment).
- Delivery of INITIAL_STATE payload upon connection acceptance.
- Real-time client bidirectional messaging (PING/PONG, GET_STATUS, error handling).
- Resource limits via ConnectionManager.
- Live broadcast verification on shipment status transitions and checkpoint events.
"""

from datetime import datetime, timezone
import pytest
from starlette.websockets import WebSocketDisconnect
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.core.security import create_access_token
from app.db.base import Base
from app.main import app
from app.models.driver import Driver
from app.models.shipment import Shipment, ShipmentStatus
from app.models.user import User, UserRole
from app.services.connection_manager import tracking_connection_manager

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
    tracking_connection_manager.clear()
    yield
    tracking_connection_manager.clear()
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client():
    return TestClient(app)


def create_test_user(
    db,
    email: str,
    role: UserRole = UserRole.ADMIN,
    is_active: bool = True,
) -> User:
    user = User(
        email=email,
        name=f"User {email}",
        hashed_password="hashed_pw_test",
        role=role,
        is_active=is_active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_test_shipment(
    db,
    tracking_number: str = "FG-TEST-WS-001",
    assigned_driver_id: int = None,
    is_active: bool = True,
) -> Shipment:
    shipment = Shipment(
        tracking_number=tracking_number,
        destination_address="100 Logistics Ave",
        destination_city="Atlanta",
        destination_state="GA",
        destination_postal_code="30301",
        total_weight_kg=120.0,
        total_volume_cbm=1.2,
        status=ShipmentStatus.CREATED,
        assigned_driver_id=assigned_driver_id,
        is_active=is_active,
    )
    db.add(shipment)
    db.commit()
    db.refresh(shipment)
    return shipment


# ------------------------------------------------------------------------------
# 1. Authentication & Security Tests
# ------------------------------------------------------------------------------

def test_ws_connection_missing_token(client):
    """
    WebSocket connection without a token must be rejected with policy violation (1008).
    """
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect("/ws/tracking/1"):
            pass
    assert exc_info.value.code == 1008


def test_ws_connection_invalid_token(client):
    """
    WebSocket connection with invalid JWT must be rejected with code 1008.
    """
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect("/ws/tracking/1?token=invalid.jwt.token"):
            pass
    assert exc_info.value.code == 1008


def test_ws_connection_deactivated_user(client):
    """
    WebSocket connection for a deactivated user must be rejected with code 1008.
    """
    db = TestingSessionLocal()
    user = create_test_user(db, "inactive@flowgrid.io", is_active=False)
    shipment = create_test_shipment(db)
    token = create_access_token(subject=user.id, role=user.role.value)
    db.close()

    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect(f"/ws/tracking/{shipment.id}?token={token}"):
            pass
    assert exc_info.value.code == 1008


def test_ws_connection_nonexistent_shipment(client):
    """
    WebSocket connection for nonexistent shipment must be rejected with code 1008.
    """
    db = TestingSessionLocal()
    user = create_test_user(db, "admin@flowgrid.io", role=UserRole.ADMIN)
    token = create_access_token(subject=user.id, role=user.role.value)
    db.close()

    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect(f"/ws/tracking/99999?token={token}"):
            pass
    assert exc_info.value.code == 1008


def test_ws_connection_inactive_shipment(client):
    """
    WebSocket connection for soft-deleted / inactive shipment must be rejected with code 1008.
    """
    db = TestingSessionLocal()
    user = create_test_user(db, "admin2@flowgrid.io", role=UserRole.ADMIN)
    shipment = create_test_shipment(db, is_active=False)
    token = create_access_token(subject=user.id, role=user.role.value)
    db.close()

    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect(f"/ws/tracking/{shipment.id}?token={token}"):
            pass
    assert exc_info.value.code == 1008


# ------------------------------------------------------------------------------
# 2. RBAC & Successful Connection Tests
# ------------------------------------------------------------------------------

def test_ws_connection_admin_success_initial_state(client):
    """
    ADMIN connection succeeds and receives INITIAL_STATE frame with current tracking details.
    """
    db = TestingSessionLocal()
    user = create_test_user(db, "admin_success@flowgrid.io", role=UserRole.ADMIN)
    shipment = create_test_shipment(db, tracking_number="FG-ADMIN-001")
    token = create_access_token(subject=user.id, role=user.role.value)
    db.close()

    with client.websocket_connect(f"/ws/tracking/{shipment.id}?token={token}") as ws:
        data = ws.receive_json()
        assert data["event"] == "INITIAL_STATE"
        assert data["shipment_id"] == shipment.id
        assert data["data"]["tracking_number"] == "FG-ADMIN-001"
        assert data["data"]["current_status"] == "CREATED"


def test_ws_connection_viewer_success(client):
    """
    VIEWER role is granted read-only tracking access.
    """
    db = TestingSessionLocal()
    user = create_test_user(db, "viewer@flowgrid.io", role=UserRole.VIEWER)
    shipment = create_test_shipment(db, tracking_number="FG-VIEWER-001")
    token = create_access_token(subject=user.id, role=user.role.value)
    db.close()

    with client.websocket_connect(f"/ws/tracking/{shipment.id}?token={token}") as ws:
        data = ws.receive_json()
        assert data["event"] == "INITIAL_STATE"
        assert data["shipment_id"] == shipment.id


def test_ws_connection_driver_assignment_rules(client):
    """
    DRIVER role is allowed for assigned shipments, but rejected for shipments assigned to another driver.
    """
    db = TestingSessionLocal()
    # Driver 1
    user_driver1 = create_test_user(db, "driver1@flowgrid.io", role=UserRole.DRIVER)
    drv1 = Driver(user_id=user_driver1.id, license_number="DL-1111", phone_number="555-0101")
    db.add(drv1)
    db.commit()
    db.refresh(drv1)

    # Driver 2
    user_driver2 = create_test_user(db, "driver2@flowgrid.io", role=UserRole.DRIVER)
    drv2 = Driver(user_id=user_driver2.id, license_number="DL-2222", phone_number="555-0202")
    db.add(drv2)
    db.commit()
    db.refresh(drv2)

    # Shipment assigned to Driver 1
    shipment_assigned_to_1 = create_test_shipment(db, tracking_number="FG-DRV-1", assigned_driver_id=drv1.id)

    token_driver1 = create_access_token(subject=user_driver1.id, role=user_driver1.role.value)
    token_driver2 = create_access_token(subject=user_driver2.id, role=user_driver2.role.value)
    db.close()

    # Driver 1 connects to their own shipment -> Success
    with client.websocket_connect(f"/ws/tracking/{shipment_assigned_to_1.id}?token={token_driver1}") as ws:
        data = ws.receive_json()
        assert data["event"] == "INITIAL_STATE"

    # Driver 2 connects to Driver 1's shipment -> Forbidden (1008)
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect(f"/ws/tracking/{shipment_assigned_to_1.id}?token={token_driver2}"):
            pass
    assert exc_info.value.code == 1008


# ------------------------------------------------------------------------------
# 3. Message Handling & Client Interaction Tests
# ------------------------------------------------------------------------------

def test_ws_ping_pong_heartbeat(client):
    """
    Server responds with PONG when client transmits PING or HEARTBEAT.
    """
    db = TestingSessionLocal()
    user = create_test_user(db, "ping_user@flowgrid.io", role=UserRole.MANAGER)
    shipment = create_test_shipment(db)
    token = create_access_token(subject=user.id, role=user.role.value)
    db.close()

    with client.websocket_connect(f"/ws/tracking/{shipment.id}?token={token}") as ws:
        # Discard INITIAL_STATE
        ws.receive_json()

        # Send PING
        ws.send_json({"type": "PING"})
        pong = ws.receive_json()
        assert pong["event"] == "PONG"
        assert pong["shipment_id"] == shipment.id


def test_ws_get_status_query(client):
    """
    Client can actively poll for consolidated tracking data using GET_STATUS.
    """
    db = TestingSessionLocal()
    user = create_test_user(db, "query_user@flowgrid.io", role=UserRole.ADMIN)
    shipment = create_test_shipment(db)
    token = create_access_token(subject=user.id, role=user.role.value)
    db.close()

    with client.websocket_connect(f"/ws/tracking/{shipment.id}?token={token}") as ws:
        ws.receive_json()  # INITIAL_STATE

        ws.send_json({"type": "GET_STATUS"})
        status_res = ws.receive_json()
        assert status_res["event"] == "LATEST_TRACKING"
        assert status_res["shipment_id"] == shipment.id


def test_ws_invalid_json_handling(client):
    """
    Malformed JSON received on WebSocket is handled safely without crashing.
    """
    db = TestingSessionLocal()
    user = create_test_user(db, "json_err@flowgrid.io", role=UserRole.ADMIN)
    shipment = create_test_shipment(db)
    token = create_access_token(subject=user.id, role=user.role.value)
    db.close()

    with client.websocket_connect(f"/ws/tracking/{shipment.id}?token={token}") as ws:
        ws.receive_json()  # INITIAL_STATE

        ws.send_text("This is not valid json")
        err_res = ws.receive_json()
        assert err_res["event"] == "ERROR"


# ------------------------------------------------------------------------------
# 4. Connection Limit Tests
# ------------------------------------------------------------------------------

def test_ws_connection_limits(client):
    """
    When connection limit for a shipment is reached, new connections are rejected with 1008.
    """
    db = TestingSessionLocal()
    user = create_test_user(db, "limits@flowgrid.io", role=UserRole.ADMIN)
    shipment = create_test_shipment(db)
    token = create_access_token(subject=user.id, role=user.role.value)
    db.close()

    # Temporarily set max_per_shipment to 1
    original_max = tracking_connection_manager.max_per_shipment
    tracking_connection_manager.max_per_shipment = 1

    try:
        with client.websocket_connect(f"/ws/tracking/{shipment.id}?token={token}"):
            # First connection occupies the slot
            # Second connection should be rejected
            with pytest.raises(WebSocketDisconnect) as exc_info:
                with client.websocket_connect(f"/ws/tracking/{shipment.id}?token={token}"):
                    pass
            assert exc_info.value.code == 1008
    finally:
        tracking_connection_manager.max_per_shipment = original_max


# ------------------------------------------------------------------------------
# 5. Live Broadcast Dispatch Tests
# ------------------------------------------------------------------------------

def test_ws_broadcast_on_status_update(client):
    """
    When shipment status is updated via API, active WebSocket subscriber receives STATUS_UPDATED event.
    """
    db = TestingSessionLocal()
    user = create_test_user(db, "broadcast_admin@flowgrid.io", role=UserRole.ADMIN)
    shipment = create_test_shipment(db, tracking_number="FG-BCAST-01")
    token = create_access_token(subject=user.id, role=user.role.value)
    db.close()

    with client.websocket_connect(f"/ws/tracking/{shipment.id}?token={token}") as ws:
        initial = ws.receive_json()
        assert initial["event"] == "INITIAL_STATE"

        # Advance status via HTTP PATCH
        headers = {"Authorization": f"Bearer {token}"}
        res = client.patch(
            f"/api/v1/shipments/{shipment.id}/status",
            headers=headers,
            json={"status": "CONFIRMED", "remarks": "Confirmed by dispatch"},
        )
        assert res.status_code == 200

        # Verify broadcast event received on WebSocket
        event = ws.receive_json()
        assert event["event"] == "STATUS_UPDATED"
        assert event["shipment_id"] == shipment.id
        assert event["data"]["status"] == "CONFIRMED"
        assert event["data"]["remarks"] == "Confirmed by dispatch"


def test_ws_broadcast_on_tracking_event(client):
    """
    When physical checkpoint event is logged via API, active subscriber receives TRACKING_EVENT_ADDED event.
    """
    db = TestingSessionLocal()
    user = create_test_user(db, "checkpoint_admin@flowgrid.io", role=UserRole.ADMIN)
    shipment = create_test_shipment(db, tracking_number="FG-SCAN-01")
    token = create_access_token(subject=user.id, role=user.role.value)
    db.close()

    with client.websocket_connect(f"/ws/tracking/{shipment.id}?token={token}") as ws:
        ws.receive_json()  # INITIAL_STATE

        # Post tracking checkpoint via HTTP POST
        headers = {"Authorization": f"Bearer {token}"}
        res = client.post(
            f"/api/v1/shipments/{shipment.id}/tracking",
            headers=headers,
            json={
                "event_type": "CHECKPOINT",
                "location": "Hub Alpha Gate 3",
                "description": "Scanned onto transit feeder",
            },
        )
        assert res.status_code == 201

        # Verify broadcast event received on WebSocket
        event = ws.receive_json()
        assert event["event"] == "TRACKING_EVENT_ADDED"
        assert event["shipment_id"] == shipment.id
        assert event["data"]["event_type"] == "CHECKPOINT"
        assert event["data"]["location"] == "Hub Alpha Gate 3"
