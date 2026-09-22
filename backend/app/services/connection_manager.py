"""
WebSocket Connection Manager
============================
Thread-safe, lightweight connection manager for tracking active WebSocket clients
subscribed to real-time shipment updates.

Features:
- Tracks active connections mapped by `shipment_id`.
- Enforces per-shipment (50) and global (1,000) connection limits to guard against DoS/resource exhaustion.
- Safe disconnect and dead-socket cleanup without reference leaks.
- Asynchronous broadcasting with graceful error handling.
- Synchronous broadcast scheduling helper for database operations and background tasks.
"""

import asyncio
from collections import defaultdict
from typing import Any, Dict, Optional, Set
from fastapi import WebSocket

from app.core.logging import get_logger

logger = get_logger("websocket_manager")

# Configurable connection limits
MAX_CONNECTIONS_PER_SHIPMENT = 50
MAX_GLOBAL_CONNECTIONS = 1000


class ConnectionManager:
    """
    Manages active WebSocket connections grouped by shipment_id.
    """

    def __init__(
        self,
        max_per_shipment: int = MAX_CONNECTIONS_PER_SHIPMENT,
        max_global: int = MAX_GLOBAL_CONNECTIONS,
    ):
        self._active_connections: Dict[int, Set[WebSocket]] = defaultdict(set)
        self._total_connections: int = 0
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self.max_per_shipment = max_per_shipment
        self.max_global = max_global

    def can_connect(self, shipment_id: int) -> bool:
        """
        Validates if connection limits allow a new client to subscribe.
        """
        if self._total_connections >= self.max_global:
            return False
        if len(self._active_connections.get(shipment_id, set())) >= self.max_per_shipment:
            return False
        return True

    async def connect(self, shipment_id: int, websocket: WebSocket) -> None:
        """
        Registers an accepted WebSocket connection to the shipment subscription pool.
        """
        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError:
            pass

        self._active_connections[shipment_id].add(websocket)
        self._total_connections += 1
        logger.info(
            "WebSocket connected for shipment_id=%d (shipment_conns=%d, total_conns=%d)",
            shipment_id,
            len(self._active_connections[shipment_id]),
            self._total_connections,
        )


    def disconnect(self, shipment_id: int, websocket: WebSocket) -> None:
        """
        Removes a WebSocket connection and cleans up empty pools.
        """
        if shipment_id in self._active_connections:
            if websocket in self._active_connections[shipment_id]:
                self._active_connections[shipment_id].discard(websocket)
                self._total_connections = max(0, self._total_connections - 1)
                logger.info(
                    "WebSocket disconnected for shipment_id=%d (remaining=%d, total=%d)",
                    shipment_id,
                    len(self._active_connections[shipment_id]),
                    self._total_connections,
                )
            if not self._active_connections[shipment_id]:
                del self._active_connections[shipment_id]

    async def broadcast_to_shipment(self, shipment_id: int, message: Dict[str, Any]) -> int:
        """
        Asynchronously broadcasts a JSON payload to all active clients subscribed to a shipment.
        Silently cleans up any dead or disconnected sockets.
        Returns the number of clients successfully notified.
        """
        if shipment_id not in self._active_connections:
            return 0

        subscribers = list(self._active_connections[shipment_id])
        if not subscribers:
            return 0

        success_count = 0
        dead_sockets = []

        for ws in subscribers:
            try:
                await ws.send_json(message)
                success_count += 1
            except Exception as exc:
                logger.warning(
                    "Failed to deliver WebSocket message on shipment_id=%d: %s",
                    shipment_id,
                    exc,
                )
                dead_sockets.append(ws)

        # Cleanup dead sockets
        for dead_ws in dead_sockets:
            self.disconnect(shipment_id, dead_ws)

        return success_count

    def broadcast_sync(self, shipment_id: int, message: Dict[str, Any]) -> None:
        """
        Non-blocking synchronous helper to schedule a broadcast on the running event loop.
        Safe to invoke from sync endpoint handlers running in thread pools or background tasks.
        """
        if self._loop and self._loop.is_running():
            try:
                asyncio.run_coroutine_threadsafe(
                    self.broadcast_to_shipment(shipment_id, message),
                    self._loop,
                )
                return
            except Exception as exc:
                logger.warning("Failed to dispatch threadsafe broadcast: %s", exc)

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.broadcast_to_shipment(shipment_id, message))
        except RuntimeError:
            pass

    def get_subscriber_count(self, shipment_id: Optional[int] = None) -> int:
        """
        Returns active subscriber count for a specific shipment or across the entire system.
        """
        if shipment_id is not None:
            return len(self._active_connections.get(shipment_id, set()))
        return self._total_connections

    def clear(self) -> None:
        """
        Resets all active connections (primarily used in test suites).
        """
        self._active_connections.clear()
        self._total_connections = 0
        self._loop = None



# Singleton connection manager instance
tracking_connection_manager = ConnectionManager()
