/**
 * FlowGrid Shipments API Service
 * ==============================
 * Endpoint mappings for /api/v1/shipments:
 * - listShipments (GET /api/v1/shipments)
 * - getShipment (GET /api/v1/shipments/{id})
 * - getShipmentByTracking (GET /api/v1/shipments/tracking/{tracking_number})
 * - createShipment (POST /api/v1/shipments)
 * - updateShipment (PUT /api/v1/shipments/{id})
 * - transitionStatus (POST /api/v1/shipments/{id}/transition)
 * - assignShipment (POST /api/v1/shipments/{id}/assign)
 */

import { apiClient } from './client.js';

export const shipmentsApi = {
  /**
   * Retrieves a paginated list of shipments with status and tracking filters.
   */
  async listShipments({ skip = 0, limit = 100, status, tracking_number, driver_id } = {}) {
    const params = new URLSearchParams({
      skip: String(skip),
      limit: String(limit),
    });
    if (status) {
      params.append('status', status);
    }
    if (tracking_number) {
      params.append('tracking_number', tracking_number);
    }
    if (driver_id !== undefined && driver_id !== null) {
      params.append('driver_id', String(driver_id));
    }
    return apiClient.get(`/api/v1/shipments?${params.toString()}`);
  },

  /**
   * Retrieves shipment details by ID.
   */
  async getShipment(shipmentId) {
    return apiClient.get(`/api/v1/shipments/${shipmentId}`);
  },

  /**
   * Retrieves shipment details using unique tracking number.
   */
  async getShipmentByTracking(trackingNumber) {
    return apiClient.get(`/api/v1/shipments/tracking/${encodeURIComponent(trackingNumber)}`);
  },

  /**
   * Creates a new shipment order (ADMIN, MANAGER).
   */
  async createShipment(payload) {
    return apiClient.post('/api/v1/shipments', payload);
  },

  /**
   * Updates shipment details before delivery (ADMIN, MANAGER).
   */
  async updateShipment(shipmentId, payload) {
    return apiClient.put(`/api/v1/shipments/${shipmentId}`, payload);
  },

  /**
   * Transitions shipment state machine (ADMIN, MANAGER).
   */
  async transitionStatus(shipmentId, { status, remarks = null }) {
    return apiClient.patch(`/api/v1/shipments/${shipmentId}/status`, {
      status,
      remarks,
    });
  },

  /**
   * Convenience alias for transitionStatus.
   */
  async updateStatus(shipmentId, { status, remarks = null }) {
    return this.transitionStatus(shipmentId, { status, remarks });
  },

  /**
   * Assigns driver and vehicle resources to shipment (ADMIN, MANAGER).
   */
  async assignShipment(shipmentId, { driver_id, vehicle_id }) {
    return apiClient.patch(`/api/v1/shipments/${shipmentId}`, {
      assigned_driver_id: driver_id,
      assigned_vehicle_id: vehicle_id,
    });
  },
};

export default shipmentsApi;
