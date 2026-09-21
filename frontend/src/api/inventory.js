/**
 * FlowGrid Inventory API Service
 * ==============================
 * Endpoint mappings for /api/v1/inventory:
 * - listInventory (GET /api/v1/inventory)
 * - getInventory (GET /api/v1/inventory/{id})
 * - createInventory (POST /api/v1/inventory)
 * - updateInventory (PUT /api/v1/inventory/{id})
 * - deleteInventory (DELETE /api/v1/inventory/{id})
 */

import { apiClient } from './client.js';

export const inventoryApi = {
  /**
   * Retrieves paginated inventory records with optional warehouse and product filters.
   */
  async listInventory({ skip = 0, limit = 100, warehouse_id, product_id } = {}) {
    const params = new URLSearchParams({
      skip: String(skip),
      limit: String(limit),
    });
    if (warehouse_id !== undefined && warehouse_id !== null) {
      params.append('warehouse_id', String(warehouse_id));
    }
    if (product_id !== undefined && product_id !== null) {
      params.append('product_id', String(product_id));
    }
    return apiClient.get(`/api/v1/inventory?${params.toString()}`);
  },

  /**
   * Retrieves a specific inventory record by ID.
   */
  async getInventory(inventoryId) {
    return apiClient.get(`/api/v1/inventory/${inventoryId}`);
  },

  /**
   * Creates a new inventory record linking product to warehouse (ADMIN, MANAGER).
   */
  async createInventory(payload) {
    return apiClient.post('/api/v1/inventory', payload);
  },

  /**
   * Updates quantity or reorder level of an inventory record (ADMIN, MANAGER).
   */
  async updateInventory(inventoryId, payload) {
    return apiClient.put(`/api/v1/inventory/${inventoryId}`, payload);
  },

  /**
   * Deletes an inventory record (ADMIN only).
   */
  async deleteInventory(inventoryId) {
    return apiClient.delete(`/api/v1/inventory/${inventoryId}`);
  },
};

export default inventoryApi;
