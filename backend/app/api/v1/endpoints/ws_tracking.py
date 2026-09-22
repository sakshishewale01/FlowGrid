"""
Real-Time Shipment Tracking WebSocket Endpoint
================================================
Provides a secure, high-performance WebSocket connection for live telemetry,
checkpoint scans, and state machine updates for active shipments.

Endpoint:
  /ws/tracking/{shipment_id}

Authentication & Authorization:
- Authenticates using standard JWT Bearer token passed via query param `?token=<jwt>`
  or fallback `Authorization` header.
- Validates active user account status.
- Enforces Role-Based Access Control (RBAC):
    * ADMIN, MANAGER, VIEWER: Full tracking visibility across all active shipments.
    * DRIVER: Permitted for their assigned freight manifests.
- Enforces shipment existence and active lifecycle state.
- Guards against resource exhaustion via ConnectionManager limits.
- Sanitizes all server logging to prevent token/secret leakage.
"""

from datetime import datetime, timezone
import json
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.core.security import decode_access_token
from app.db.session import SessionLocal
from app.models.user import User, UserRole
from app.models.shipment import Shipment
from app.services.connection_manager import tracking_connection_manager
from app.services.tracking_service import tracking_service

logger = get_logger("ws_tracking")
router = APIRouter()


def _extract_token_from_websocket(websocket: WebSocket) -> Optional[str]:
    """
    Safely extracts JWT token from query parameters, Authorization header,
    or Sec-WebSocket-Protocol without logging credentials.
    """
    # 1. Query parameter: ?token=<jwt> (Primary standard for browser WebSockets)
    token = websocket.query_params.get("token")
    if token and token.strip():
        return token.strip()

    # 2. Authorization header: Bearer <jwt>
    auth_header = websocket.headers.get("authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        return auth_header[7:].strip()

    # 3. Sec-WebSocket-Protocol fallback
    protocols = websocket.headers.get("sec-websocket-protocol")
    if protocols:
        for proto in protocols.split(","):
            cleaned = proto.strip()
            if cleaned and cleaned.lower() != "bearer":
                return cleaned

    return None


def _authenticate_ws_user(token: str, db: Session) -> Optional[User]:
    """
    Decodes the JWT token and verifies user existence and active status.
    Returns User instance or None if invalid.
    """
    payload = decode_access_token(token)
    if not payload:
        return None

    user_id_raw = payload.get("sub")
    if not user_id_raw:
        return None

    try:
        user_id = int(user_id_raw)
    except (ValueError, TypeError):
        return None

    user = db.get(User, user_id)
    if not user or not user.is_active:
        return None

    return user


def _check_shipment_permission(user: User, shipment: Shipment) -> bool:
    """
    Enforces FlowGrid RBAC rules for accessing shipment tracking:
    - ADMIN, MANAGER, VIEWER: Granted access to all active shipments.
    - DRIVER: Granted access if assigned to this shipment or unassigned manifest.
    """
    if user.role in (UserRole.ADMIN, UserRole.MANAGER, UserRole.VIEWER):
        return True

    if user.role == UserRole.DRIVER:
        # If assigned to a driver, verify it matches current user's driver record
        if shipment.assigned_driver_id is not None:
            if hasattr(user, "driver") and user.driver and user.driver.id == shipment.assigned_driver_id:
                return True
            return False
        # If unassigned, allow field drivers to observe available manifest
        return True

    return False


def _get_db_session() -> Session:
    from app.main import app
    from app.api.deps import get_db
    if hasattr(app, "dependency_overrides") and get_db in app.dependency_overrides:
        override = app.dependency_overrides[get_db]
        gen = override()
        return next(gen)
    return SessionLocal()


@router.websocket("/ws/tracking/{shipment_id}")
async def tracking_websocket_endpoint(
    websocket: WebSocket,
    shipment_id: int,
):
    """
    Real-time tracking WebSocket connection for a specific shipment.
    Rejects invalid/unauthorized connections with code 1008 (Policy Violation).
    """
    token = _extract_token_from_websocket(websocket)
    if not token:
        logger.warning("Rejected WebSocket connection: missing authentication token")
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Authentication token required",
        )
        return

    # Check connection limits before database work
    if not tracking_connection_manager.can_connect(shipment_id):
        logger.warning(
            "Rejected WebSocket connection for shipment_id=%d: connection limit reached",
            shipment_id,
        )
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Connection limit exceeded",
        )
        return

    # Database validation session
    db: Session = _get_db_session()

    try:
        user = _authenticate_ws_user(token, db)
        if not user:
            logger.warning("Rejected WebSocket connection: invalid or expired token")
            await websocket.close(
                code=status.WS_1008_POLICY_VIOLATION,
                reason="Invalid authentication credentials",
            )
            return

        shipment = db.get(Shipment, shipment_id)
        if not shipment or not shipment.is_active:
            logger.warning(
                "Rejected WebSocket connection: shipment_id=%d not found or inactive",
                shipment_id,
            )
            await websocket.close(
                code=status.WS_1008_POLICY_VIOLATION,
                reason="Shipment not found or inactive",
            )
            return

        if not _check_shipment_permission(user, shipment):
            logger.warning(
                "Rejected WebSocket connection: user_id=%d role=%s forbidden for shipment_id=%d",
                user.id,
                user.role.value,
                shipment_id,
            )
            await websocket.close(
                code=status.WS_1008_POLICY_VIOLATION,
                reason="Access forbidden for this shipment",
            )
            return

        # Prepare initial state payload
        try:
            latest_info = tracking_service.get_latest_tracking_info(db, shipment_id)
            initial_data = latest_info.model_dump(mode="json")
        except Exception:
            initial_data = {
                "shipment_id": shipment.id,
                "tracking_number": shipment.tracking_number,
                "current_status": shipment.status.value,
            }
    finally:
        db.close()

    # Accept connection
    await websocket.accept()
    await tracking_connection_manager.connect(shipment_id, websocket)

    try:
        # Deliver initial state frame
        await websocket.send_json(
            {
                "event": "INITIAL_STATE",
                "shipment_id": shipment_id,
                "data": initial_data,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

        # Inbound message loop (heartbeats, client pings, queries)
        while True:
            raw_text = await websocket.receive_text()
            try:
                payload = json.loads(raw_text)
                msg_type = (
                    payload.get("type")
                    or payload.get("action")
                    or payload.get("event")
                    or ""
                ).upper()

                if msg_type in ("PING", "HEARTBEAT"):
                    await websocket.send_json(
                        {
                            "event": "PONG",
                            "shipment_id": shipment_id,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                    )
                elif msg_type == "GET_STATUS":
                    # Refresh tracking state on demand
                    fresh_db = _get_db_session()

                    try:
                        fresh_info = tracking_service.get_latest_tracking_info(fresh_db, shipment_id)
                        await websocket.send_json(
                            {
                                "event": "LATEST_TRACKING",
                                "shipment_id": shipment_id,
                                "data": fresh_info.model_dump(mode="json"),
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                            }
                        )
                    finally:
                        fresh_db.close()
                else:
                    await websocket.send_json(
                        {
                            "event": "ACK",
                            "shipment_id": shipment_id,
                            "message": "Message received",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                    )
            except json.JSONDecodeError:
                await websocket.send_json(
                    {
                        "event": "ERROR",
                        "detail": "Invalid JSON frame received",
                    }
                )
    except WebSocketDisconnect:
        logger.info("Client cleanly disconnected from shipment_id=%d", shipment_id)
    except Exception as exc:
        logger.warning(
            "WebSocket connection closed abnormally for shipment_id=%d: %s",
            shipment_id,
            exc,
        )
    finally:
        tracking_connection_manager.disconnect(shipment_id, websocket)
