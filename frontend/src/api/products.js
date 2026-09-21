/**
 * FlowGrid Products API Service
 * =============================
 * Endpoint mappings for /api/v1/products:
 * - listProducts (GET /api/v1/products)
 * - getProduct (GET /api/v1/products/{id})
 * - createProduct (POST /api/v1/products)
 * - updateProduct (PUT /api/v1/products/{id})
 * - deleteProduct (DELETE /api/v1/products/{id})
 */

import { apiClient } from './client.js';

export const productsApi = {
  /**
   * Retrieves a paginated list of catalog products.
   */
  async listProducts({ skip = 0, limit = 100, is_active } = {}) {
    const params = new URLSearchParams({
      skip: String(skip),
      limit: String(limit),
    });
    if (is_active !== undefined && is_active !== null) {
      params.append('is_active', String(is_active));
    }
    return apiClient.get(`/api/v1/products?${params.toString()}`);
  },

  /**
   * Retrieves a specific product by primary key ID.
   */
  async getProduct(productId) {
    return apiClient.get(`/api/v1/products/${productId}`);
  },

  /**
   * Registers a new product item (ADMIN, MANAGER).
   */
  async createProduct(payload) {
    return apiClient.post('/api/v1/products', payload);
  },

  /**
   * Updates attributes of an existing product (ADMIN, MANAGER).
   */
  async updateProduct(productId, payload) {
    return apiClient.put(`/api/v1/products/${productId}`, payload);
  },

  /**
   * Deletes a catalog product item (ADMIN only).
   */
  async deleteProduct(productId) {
    return apiClient.delete(`/api/v1/products/${productId}`);
  },
};

export default productsApi;
