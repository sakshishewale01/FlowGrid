/**
 * FlowGrid Shipment Tracking API Service
 * ======================================
 * Endpoint mappings for shipment tracking and waypoint checkpoints:
 * - getStatusHistory (GET /api/v1/shipments/{id}/history)
 * - addTrackingEvent (POST /api/v1/shipments/{id}/tracking)
 * - getTrackingEvents (GET /api/v1/shipments/{id}/tracking)
 * - getLatestTrackingInfo (GET /api/v1/shipments/{id}/tracking/latest)
 * - lookupByTrackingNumber (GET /api/v1/shipments/tracking/{tracking_number})
 */

import { apiClient } from './client.js';

export const trackingApi = {
  /**
   * Retrieves complete lifecycle audit history of status transitions.
   */
  async getStatusHistory(shipmentId, { skip = 0, limit = 100 } = {}) {
    const params = new URLSearchParams({
      skip: String(skip),
      limit: String(limit),
    });
    return apiClient.get(`/api/v1/shipments/${shipmentId}/history?${params.toString()}`);
  },

  /**
   * Records a new physical tracking event / waypoint milestone (ADMIN, MANAGER).
   */
  async addTrackingEvent(shipmentId, { status, location, notes = null }) {
    return apiClient.post(`/api/v1/shipments/${shipmentId}/tracking`, {
      status,
      location,
      notes,
    });
  },

  /**
   * Retrieves all recorded physical tracking events for a shipment.
   */
  async getTrackingEvents(shipmentId, { skip = 0, limit = 100 } = {}) {
    const params = new URLSearchParams({
      skip: String(skip),
      limit: String(limit),
    });
    return apiClient.get(`/api/v1/shipments/${shipmentId}/tracking?${params.toString()}`);
  },

  /**
   * Retrieves consolidated real-time tracking info (state, last status change, latest event).
   */
  async getLatestTrackingInfo(shipmentId) {
    return apiClient.get(`/api/v1/shipments/${shipmentId}/tracking/latest`);
  },

  /**
   * Directly look up a shipment and tracking status by public tracking number.
   */
  async lookupByTrackingNumber(trackingNumber) {
    return apiClient.get(`/api/v1/shipments/tracking/${encodeURIComponent(trackingNumber)}`);
  },
};

export default trackingApi;
