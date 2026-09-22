/**
 * FlowGrid In-App Notification Context
 * =====================================
 * Manages client-side notifications for shipment lifecycle events,
 * inventory low-stock warnings, and system alerts.
 *
 * Core Capabilities:
 * - Unread count and local mark-as-read / dismiss actions.
 * - Deduplication preventing repeated identical alert cards.
 * - LocalStorage persistence for user read state.
 * - Background synchronization for low-stock inventory violations.
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useAuth } from './AuthContext';
import { analyticsApi } from '../api/analytics';

const NOTIFICATIONS_STORAGE_KEY = 'flowgrid_notifications_v1';

const NotificationContext = createContext(null);

export function NotificationProvider({ children }) {
  const { isAuthenticated } = useAuth();
  const [notifications, setNotifications] = useState(() => {
    try {
      const stored = localStorage.getItem(NOTIFICATIONS_STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        return Array.isArray(parsed) ? parsed : [];
      }
    } catch {
      // Storage unavailable or corrupted
    }
    return [];
  });

  // Save to localStorage whenever notifications change
  useEffect(() => {
    try {
      localStorage.setItem(NOTIFICATIONS_STORAGE_KEY, JSON.stringify(notifications));
    } catch {
      // Ignore
    }
  }, [notifications]);

  /**
   * Add a notification with deduplication.
   * If an item with the same ID already exists:
   * - If it was read and new event arrived, mark unread and update timestamp.
   * - Otherwise ignore to prevent noisy duplicates.
   */
  const addNotification = useCallback((newNotif) => {
    if (!newNotif || !newNotif.id) return;

    setNotifications((prev) => {
      const existingIndex = prev.findIndex((n) => n.id === newNotif.id);
      if (existingIndex >= 0) {
        const existing = prev[existingIndex];
        // If content is identical and still unread, don't duplicate
        if (!existing.read && existing.message === newNotif.message) {
          return prev;
        }
        // Update existing notification
        const updated = [...prev];
        updated[existingIndex] = {
          ...existing,
          ...newNotif,
          read: false,
          timestamp: newNotif.timestamp || new Date().toISOString(),
        };
        return updated;
      }

      // Add to top of list (newest first, capped at 100 entries)
      return [
        {
          read: false,
          timestamp: new Date().toISOString(),
          ...newNotif,
        },
        ...prev.slice(0, 99),
      ];
    });
  }, []);

  /**
   * Helper to dispatch shipment status transition alerts.
   */
  const notifyShipmentStatus = useCallback(
    ({ shipmentId, trackingNumber, status, remarks }) => {
      const severity =
        status === 'FAILED' ? 'error' : status === 'DELIVERED' ? 'success' : 'info';
      const cleanStatus = status ? status.replace(/_/g, ' ') : 'Updated';

      addNotification({
        id: `shipment_${shipmentId}_${status}`,
        type: 'SHIPMENT',
        severity,
        title: `Shipment ${cleanStatus}`,
        message: `Manifest #${trackingNumber || shipmentId} transitioned to ${cleanStatus}${
          remarks ? `: ${remarks}` : ''
        }`,
        metadata: { shipmentId, trackingNumber, status },
        timestamp: new Date().toISOString(),
      });
    },
    [addNotification]
  );

  /**
   * Scan for low-stock inventory warnings from analytics data.
   */
  const checkInventoryAlerts = useCallback(async () => {
    if (!isAuthenticated) return;
    try {
      const data = await analyticsApi.getInventoryAnalytics();
      if (data && Array.isArray(data.low_stock_items)) {
        data.low_stock_items.forEach((item) => {
          addNotification({
            id: `low_stock_${item.product_id}_${item.warehouse_id}`,
            type: 'LOW_STOCK',
            severity: 'warning',
            title: `Low Stock: ${item.product_name}`,
            message: `SKU ${item.sku} at ${item.warehouse_name} has ${item.quantity} units remaining (reorder threshold: ${item.reorder_threshold}).`,
            metadata: {
              productId: item.product_id,
              warehouseId: item.warehouse_id,
              sku: item.sku,
            },
            timestamp: new Date().toISOString(),
          });
        });
      }
    } catch {
      // Analytics not available or network error - ignore gracefully
    }
  }, [isAuthenticated, addNotification]);

  // Synchronize inventory alerts on authentication
  useEffect(() => {
    if (isAuthenticated) {
      checkInventoryAlerts();
    }
  }, [isAuthenticated, checkInventoryAlerts]);

  const markAsRead = useCallback((id) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, read: true } : n))
    );
  }, []);

  const markAllAsRead = useCallback(() => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  }, []);

  const clearNotification = useCallback((id) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  }, []);

  const clearAll = useCallback(() => {
    setNotifications([]);
  }, []);

  const unreadCount = notifications.filter((n) => !n.read).length;

  const value = {
    notifications,
    unreadCount,
    addNotification,
    notifyShipmentStatus,
    checkInventoryAlerts,
    markAsRead,
    markAllAsRead,
    clearNotification,
    clearAll,
  };

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  );
}

export function useNotifications() {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotifications must be used within a NotificationProvider');
  }
  return context;
}

export default NotificationContext;
