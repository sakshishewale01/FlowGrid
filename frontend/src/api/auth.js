/**
 * FlowGrid Authentication API Endpoints
 * =====================================
 * Wraps FastAPI authentication endpoints:
 * - POST /api/v1/auth/login
 * - POST /api/v1/auth/register
 * - GET  /api/v1/auth/me
 * - GET  /health
 */

import { apiClient } from './client';

export const authApi = {
  /**
   * Authenticate user with email and password.
   *
   * @param {Object} credentials - { email, password }
   * @returns {Promise<{ access_token: string, token_type: string, user: Object }>}
   */
  async login({ email, password }) {
    return apiClient.post('/api/v1/auth/login', {
      email: email.trim(),
      password,
    });
  },

  /**
   * Register a new user account.
   *
   * @param {Object} payload - { name, email, password, role }
   * @returns {Promise<Object>} The created User profile
   */
  async register({ name, email, password, role = 'VIEWER' }) {
    return apiClient.post('/api/v1/auth/register', {
      name: name.trim(),
      email: email.trim(),
      password,
      role,
    });
  },

  /**
   * Fetch current authenticated user's profile.
   *
   * @returns {Promise<Object>} The User profile
   */
  async getMe() {
    return apiClient.get('/api/v1/auth/me');
  },

  /**
   * Ping backend operational health check endpoint.
   *
   * @returns {Promise<{ status: string, application: string }>}
   */
  async checkHealth() {
    return apiClient.get('/health');
  },
};

export default authApi;
