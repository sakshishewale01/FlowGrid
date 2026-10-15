/**
 * FlowGrid Assistant API Service
 * ==============================
 * Endpoint mappings for /api/v1/assistant:
 * - query (POST /api/v1/assistant/query)
 */

import { apiClient } from './client.js';

export const assistantApi = {
  /**
   * Queries the grounded FlowGrid Logistics Assistant.
   *
   * @param {string} queryText - Natural language query
   * @returns {Promise<Object>} AssistantQueryResponse
   */
  async query(queryText) {
    return apiClient.post('/api/v1/assistant/query', {
      query: queryText,
    });
  },
};

export default assistantApi;
