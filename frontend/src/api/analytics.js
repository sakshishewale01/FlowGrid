/**
 * FlowGrid Analytics API Service
 * ==============================
 * Endpoint mappings for /api/v1/analytics:
 * - getOverview (GET /api/v1/analytics/overview)
 * - getShipmentAnalytics (GET /api/v1/analytics/shipments)
 * - getInventoryAnalytics (GET /api/v1/analytics/inventory)
 * - getWarehouseAnalytics (GET /api/v1/analytics/warehouses)
 * - getRouteAnalytics (GET /api/v1/analytics/routes)
 */

import { apiClient } from './client.js';

export const analyticsApi = {
  /**
   * Retrieves high-level operational KPIs spanning shipments, facilities, products, drivers, and routes.
   */
  async getOverview({ start_date, end_date } = {}) {
    const params = new URLSearchParams();
    if (start_date) params.append('start_date', start_date);
    if (end_date) params.append('end_date', end_date);
    const qs = params.toString() ? `?${params.toString()}` : '';
    return apiClient.get(`/api/v1/analytics/overview${qs}`);
  },

  /**
   * Retrieves shipment lifecycle distribution, daily volume, completion rate, and exceptions.
   */
  async getShipmentAnalytics({ start_date, end_date } = {}) {
    const params = new URLSearchParams();
    if (start_date) params.append('start_date', start_date);
    if (end_date) params.append('end_date', end_date);
    const qs = params.toString() ? `?${params.toString()}` : '';
    return apiClient.get(`/api/v1/analytics/shipments${qs}`);
  },

  /**
   * Retrieves gross inventory balances, safety stock threshold violations, and facility breakdown.
   */
  async getInventoryAnalytics() {
    return apiClient.get('/api/v1/analytics/inventory');
  },

  /**
   * Retrieves network-wide warehouse counts (active vs inactive) and facility capacity profiles.
   */
  async getWarehouseAnalytics() {
    return apiClient.get('/api/v1/analytics/warehouses');
  },

  /**
   * Retrieves freight corridor status distributions, active vs completed counts, and shipment allocations.
   */
  async getRouteAnalytics({ start_date, end_date } = {}) {
    const params = new URLSearchParams();
    if (start_date) params.append('start_date', start_date);
    if (end_date) params.append('end_date', end_date);
    const qs = params.toString() ? `?${params.toString()}` : '';
    return apiClient.get(`/api/v1/analytics/routes${qs}`);
  },
};

export default analyticsApi;
