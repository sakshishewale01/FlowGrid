/**
 * FlowGrid Warehouses API Service
 * ===============================
 * Endpoint mappings for /api/v1/warehouses:
 * - listWarehouses (GET /api/v1/warehouses)
 * - getWarehouse (GET /api/v1/warehouses/{id})
 * - createWarehouse (POST /api/v1/warehouses)
 * - updateWarehouse (PUT /api/v1/warehouses/{id})
 * - deleteWarehouse (DELETE /api/v1/warehouses/{id})
 */

import { apiClient } from './client.js';

export const warehousesApi = {
  /**
   * Retrieves a paginated list of warehouses.
   */
  async listWarehouses({ skip = 0, limit = 100, is_active } = {}) {
    const params = new URLSearchParams({
      skip: String(skip),
      limit: String(limit),
    });
    if (is_active !== undefined && is_active !== null) {
      params.append('is_active', String(is_active));
    }
    return apiClient.get(`/api/v1/warehouses?${params.toString()}`);
  },

  /**
   * Retrieves details for a specific warehouse by ID.
   */
  async getWarehouse(warehouseId) {
    return apiClient.get(`/api/v1/warehouses/${warehouseId}`);
  },

  /**
   * Registers a new warehouse facility (ADMIN, MANAGER).
   */
  async createWarehouse(payload) {
    return apiClient.post('/api/v1/warehouses', payload);
  },

  /**
   * Updates attributes of an existing warehouse (ADMIN, MANAGER).
   */
  async updateWarehouse(warehouseId, payload) {
    return apiClient.put(`/api/v1/warehouses/${warehouseId}`, payload);
  },

  /**
   * Deletes a warehouse facility (ADMIN only).
   */
  async deleteWarehouse(warehouseId) {
    return apiClient.delete(`/api/v1/warehouses/${warehouseId}`);
  },
};

export default warehousesApi;
