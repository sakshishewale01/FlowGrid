/**
 * FlowGrid Machine Learning API Service
 * =====================================
 * Endpoint mappings for /api/v1/ml:
 * - predictDelay (POST /api/v1/ml/predict-delay)
 */

import { apiClient } from './client.js';

export const mlApi = {
  /**
   * Predicts shipment delay probability, qualitative risk level, and classification
   * using the trained India corridor Random Forest model artifact.
   * Strictly decoupled: does not persist records to PostgreSQL.
   *
   * @param {Object} payload
   * @param {string} payload.warehouse - Origin warehouse facility name
   * @param {string} payload.destination - Destination commercial/depot hub
   * @param {string} payload.transport_mode - Vehicle class
   * @param {number} payload.distance_km - Verified corridor distance in kilometers
   * @param {string} payload.supplier - Logistics carrier / supplier partner
   * @param {string} payload.driver - Assigned driver alias
   * @param {string} [payload.dispatch_date] - Calendar date (YYYY-MM-DD)
   * @param {number} [payload.month] - Optional explicit month (1-12)
   * @param {number} [payload.day_of_week] - Optional explicit day of week (0-6)
   * @returns {Promise<Object>} DelayPredictionResponse
   */
  async predictDelay(payload) {
    return apiClient.post('/api/v1/ml/predict-delay', payload);
  },
};

export default mlApi;
