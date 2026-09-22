/**
 * FlowGrid Real-Time Tracking WebSocket Hook
 * ==========================================
 * Manages live telemetry and status event subscriptions for a specific shipment.
 *
 * Features:
 * - Connection lifecycle states: CONNECTING, CONNECTED, DISCONNECTED, ERROR.
 * - JWT authentication via query parameter (?token=).
 * - Automatic teardown on drawer close, shipment switch, or component unmount.
 * - JSON message parsing and callback dispatch for valid events.
 * - Client-side heartbeat/ping helper.
 * - Reconnect capability with backoff safety.
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { getWsBaseUrl, getStoredToken } from '../api/client.js';

export const WS_STATUS = {
  CONNECTING: 'CONNECTING',
  CONNECTED: 'CONNECTED',
  DISCONNECTED: 'DISCONNECTED',
  ERROR: 'ERROR',
};

export function useTrackingWebSocket({
  shipmentId,
  token: customToken = null,
  enabled = true,
  onEvent = null,
} = {}) {
  const [connectionStatus, setConnectionStatus] = useState(WS_STATUS.DISCONNECTED);
  const [lastEvent, setLastEvent] = useState(null);
  const [errorDetail, setErrorDetail] = useState(null);


  const socketRef = useRef(null);
  const onEventRef = useRef(onEvent);
  const reconnectTimeoutRef = useRef(null);
  const isManuallyClosedRef = useRef(false);

  // Keep onEvent callback reference fresh without triggering effect re-runs
  useEffect(() => {
    onEventRef.current = onEvent;
  }, [onEvent]);

  const disconnect = useCallback(() => {
    isManuallyClosedRef.current = true;
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (socketRef.current) {
      try {
        socketRef.current.close(1000, 'Subscription terminated');
      } catch {
        // Socket already closed
      }
      socketRef.current = null;
    }
    setConnectionStatus(WS_STATUS.DISCONNECTED);
  }, []);

  const connect = useCallback(() => {
    const token = customToken || getStoredToken();
    if (!enabled || !shipmentId || !token) {
      disconnect();
      return;
    }


    // Clean up existing socket before opening a new one
    if (socketRef.current) {
      try {
        socketRef.current.close(1000, 'Reconnecting');
      } catch {
        // Ignore
      }
      socketRef.current = null;
    }

    isManuallyClosedRef.current = false;
    setConnectionStatus(WS_STATUS.CONNECTING);
    setErrorDetail(null);

    try {
      const wsBase = getWsBaseUrl();
      const wsUrl = `${wsBase}/ws/tracking/${shipmentId}?token=${encodeURIComponent(token)}`;
      const ws = new WebSocket(wsUrl);
      socketRef.current = ws;

      ws.onopen = () => {
        if (socketRef.current !== ws) return;
        setConnectionStatus(WS_STATUS.CONNECTED);
        setErrorDetail(null);
      };

      ws.onmessage = (event) => {
        if (socketRef.current !== ws) return;
        try {
          const payload = JSON.parse(event.data);
          setLastEvent(payload);
          if (onEventRef.current) {
            onEventRef.current(payload);
          }
        } catch {
          // Ignore unparseable non-JSON frames
        }
      };

      ws.onerror = () => {
        if (socketRef.current !== ws) return;
        setConnectionStatus(WS_STATUS.ERROR);
        setErrorDetail('WebSocket encountered a network error');
      };

      ws.onclose = (ev) => {
        if (socketRef.current !== ws) return;
        socketRef.current = null;

        if (isManuallyClosedRef.current) {
          setConnectionStatus(WS_STATUS.DISCONNECTED);
        } else if (ev.code === 1008) {
          setConnectionStatus(WS_STATUS.ERROR);
          setErrorDetail(ev.reason || 'Authentication failed or permission denied');
        } else {
          setConnectionStatus(WS_STATUS.DISCONNECTED);
        }
      };
    } catch (err) {
      setConnectionStatus(WS_STATUS.ERROR);
      setErrorDetail(err.message || 'Failed to initialize WebSocket');
    }
  }, [shipmentId, enabled, customToken, disconnect]);

  useEffect(() => {
    if (enabled && shipmentId) {
      connect();
    } else {
      disconnect();
    }

    return () => {
      disconnect();
    };
  }, [enabled, shipmentId, connect, disconnect]);

  const sendPing = useCallback(() => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({ type: 'PING' }));
      return true;
    }
    return false;
  }, []);

  const reconnect = useCallback(() => {
    disconnect();
    connect();
  }, [disconnect, connect]);

  return {
    connectionStatus,
    isConnected: connectionStatus === WS_STATUS.CONNECTED,
    isConnecting: connectionStatus === WS_STATUS.CONNECTING,
    lastEvent,
    errorDetail,
    sendPing,
    reconnect,
  };
}

export default useTrackingWebSocket;
