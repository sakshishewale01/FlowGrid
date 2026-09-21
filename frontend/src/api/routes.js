/**
 * FlowGrid Routes API Service
 * ===========================
 * Endpoint mappings for /api/v1/routes:
 * - listRoutes (GET /api/v1/routes)
 * - getRoute (GET /api/v1/routes/{id})
 * - createRoute (POST /api/v1/routes)
 * - updateRoute (PUT /api/v1/routes/{id})
 * - deleteRoute (DELETE /api/v1/routes/{id})
 * - assignShipmentToRoute (POST /api/v1/routes/{id}/shipments)
 * - removeShipmentFromRoute (DELETE /api/v1/routes/{id}/shipments/{shipment_id})
 */

import { apiClient } from './client.js';

export const routesApi = {
  /**
   * Retrieves paginated list of transit routes and corridors.
   */
  async listRoutes({ skip = 0, limit = 100, status, is_active, search } = {}) {
    const params = new URLSearchParams({
      skip: String(skip),
      limit: String(limit),
    });
    if (status) {
      params.append('status', status);
    }
    if (is_active !== undefined && is_active !== null) {
      params.append('is_active', String(is_active));
    }
    if (search) {
      params.append('search', search);
    }
    return apiClient.get(`/api/v1/routes?${params.toString()}`);
  },

  /**
   * Retrieves route by primary key ID.
   */
  async getRoute(routeId) {
    return apiClient.get(`/api/v1/routes/${routeId}`);
  },

  /**
   * Creates a new route record (ADMIN, MANAGER).
   */
  async createRoute(payload) {
    return apiClient.post('/api/v1/routes', payload);
  },

  /**
   * Updates route details (ADMIN, MANAGER).
   */
  async updateRoute(routeId, payload) {
    return apiClient.put(`/api/v1/routes/${routeId}`, payload);
  },

  /**
   * Deletes a route record (ADMIN only).
   */
  async deleteRoute(routeId) {
    return apiClient.delete(`/api/v1/routes/${routeId}`);
  },

  /**
   * Assigns a shipment to a route corridor (ADMIN, MANAGER).
   */
  async assignShipmentToRoute(routeId, shipmentId) {
    return apiClient.post(`/api/v1/routes/${routeId}/shipments`, {
      shipment_id: shipmentId,
    });
  },

  /**
   * Removes a shipment assignment from a route corridor (ADMIN, MANAGER).
   */
  async removeShipmentFromRoute(routeId, shipmentId) {
    return apiClient.delete(`/api/v1/routes/${routeId}/shipments/${shipmentId}`);
  },
};

export default routesApi;
