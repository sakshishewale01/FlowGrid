/**
 * FlowGrid Drivers API Service
 * ============================
 * Endpoint mappings for /api/v1/drivers:
 * - listDrivers (GET /api/v1/drivers)
 * - getDriver (GET /api/v1/drivers/{id})
 * - createDriver (POST /api/v1/drivers)
 * - updateDriver (PUT /api/v1/drivers/{id})
 * - deleteDriver (DELETE /api/v1/drivers/{id})
 */

import { apiClient } from './client.js';

export const driversApi = {
  /**
   * Retrieves paginated list of driver profiles.
   */
  async listDrivers({ skip = 0, limit = 100, availability_status, is_active } = {}) {
    const params = new URLSearchParams({
      skip: String(skip),
      limit: String(limit),
    });
    if (availability_status) {
      params.append('availability_status', availability_status);
    }
    if (is_active !== undefined && is_active !== null) {
      params.append('is_active', String(is_active));
    }
    return apiClient.get(`/api/v1/drivers?${params.toString()}`);
  },

  /**
   * Retrieves specific driver profile by ID.
   */
  async getDriver(driverId) {
    return apiClient.get(`/api/v1/drivers/${driverId}`);
  },

  /**
   * Registers a new driver profile linked to a user (ADMIN, MANAGER).
   */
  async createDriver(payload) {
    return apiClient.post('/api/v1/drivers', payload);
  },

  /**
   * Updates driver license, phone, or status (ADMIN, MANAGER).
   */
  async updateDriver(driverId, payload) {
    return apiClient.put(`/api/v1/drivers/${driverId}`, payload);
  },

  /**
   * Deletes a driver profile (ADMIN only).
   */
  async deleteDriver(driverId) {
    return apiClient.delete(`/api/v1/drivers/${driverId}`);
  },
};

export default driversApi;
