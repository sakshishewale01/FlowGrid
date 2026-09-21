/**
 * FlowGrid API Services Index
 * ===========================
 * Central aggregation of all client API domain services.
 */

export { apiClient, apiFetch, ApiError, formatErrorMessage, TOKEN_STORAGE_KEY } from './client.js';
export { authApi } from './auth.js';
export { warehousesApi } from './warehouses.js';
export { productsApi } from './products.js';
export { inventoryApi } from './inventory.js';
export { driversApi } from './drivers.js';
export { vehiclesApi } from './vehicles.js';
export { shipmentsApi } from './shipments.js';
export { trackingApi } from './tracking.js';
export { routesApi } from './routes.js';
export { analyticsApi } from './analytics.js';
