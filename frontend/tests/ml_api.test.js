import test from 'node:test';
import assert from 'node:assert/strict';

import { mlApi, apiClient } from '../src/api/index.js';

const API_URL = 'http://127.0.0.1:8000';

test('ML API: mlApi is properly exported and defines predictDelay', () => {
  assert.ok(mlApi, 'mlApi should be defined');
  assert.equal(typeof mlApi.predictDelay, 'function', 'predictDelay must be a function');
});

test('ML API: Integration test against POST /api/v1/ml/predict-delay', async (t) => {
  // 1. Verify backend health
  let isAvailable = false;
  try {
    const health = await fetch(`${API_URL}/health`, { signal: AbortSignal.timeout(1500) });
    isAvailable = health.ok;
  } catch {
    isAvailable = false;
  }

  if (!isAvailable) {
    t.skip('FastAPI backend server is not available at ' + API_URL);
    return;
  }

  // 2. Obtain valid auth token
  const loginRes = await fetch(`${API_URL}/api/v1/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email: 'manager@flowgrid.io',
      password: 'ManagerPass123!',
    }),
  });

  if (!loginRes.ok) {
    t.skip('Could not log in to retrieve auth token');
    return;
  }

  const { access_token } = await loginRes.json();
  assert.ok(access_token, 'Should receive access token');

  // 3. Test predictDelay endpoint via authenticated fetch
  const payload = {
    warehouse: 'East Depot - Kolkata',
    destination: 'Jaipur Commerce Center',
    transport_mode: 'Mini Truck (Tata Ace class)',
    distance_km: 1765.1,
    supplier: 'Orion Freight Co.',
    driver: 'A. Kumar',
    dispatch_date: '2026-10-15',
  };

  const predictRes = await fetch(`${API_URL}/api/v1/ml/predict-delay`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${access_token}`,
    },
    body: JSON.stringify(payload),
  });

  assert.equal(predictRes.status, 200, 'Predict endpoint should return HTTP 200');
  const data = await predictRes.json();

  // 4. Assert structured response fields
  assert.equal(typeof data.is_delayed, 'boolean');
  assert.equal(typeof data.delay_probability, 'number');
  assert.ok(data.delay_probability >= 0.0 && data.delay_probability <= 1.0);
  assert.ok(['LOW', 'MEDIUM', 'HIGH'].includes(data.risk_level));
  assert.ok(data.explanation.includes('Prototype notice'));
  assert.equal(data.features_used.warehouse, 'East Depot - Kolkata');
  assert.equal(data.features_used.distance_km, 1765.1);
});
