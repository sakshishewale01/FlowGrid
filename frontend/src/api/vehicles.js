/**
 * FlowGrid Vehicles API Service
 * =============================
 * Endpoint mappings for /api/v1/vehicles:
 * - listVehicles (GET /api/v1/vehicles)
 * - getVehicle (GET /api/v1/vehicles/{id})
 * - createVehicle (POST /api/v1/vehicles)
 * - updateVehicle (PUT /api/v1/vehicles/{id})
 * - deleteVehicle (DELETE /api/v1/vehicles/{id})
 */

import { apiClient } from './client.js';

export const vehiclesApi = {
  /**
   * Retrieves paginated list of fleet transport units.
   */
  async listVehicles({ skip = 0, limit = 100, status, is_active } = {}) {
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
    return apiClient.get(`/api/v1/vehicles?${params.toString()}`);
  },

  /**
   * Retrieves specific vehicle details by primary key ID.
   */
  async getVehicle(vehicleId) {
    return apiClient.get(`/api/v1/vehicles/${vehicleId}`);
  },

  /**
   * Registers a new fleet vehicle (ADMIN, MANAGER).
   */
  async createVehicle(payload) {
    return apiClient.post('/api/v1/vehicles', payload);
  },

  /**
   * Modifies vehicle attributes, type, capacity, or status (ADMIN, MANAGER).
   */
  async updateVehicle(vehicleId, payload) {
    return apiClient.put(`/api/v1/vehicles/${vehicleId}`, payload);
  },

  /**
   * Deletes a vehicle record (ADMIN only).
   */
  async deleteVehicle(vehicleId) {
    return apiClient.delete(`/api/v1/vehicles/${vehicleId}`);
  },
};

export default vehiclesApi;
