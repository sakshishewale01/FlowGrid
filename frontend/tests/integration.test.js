import test from 'node:test';
import assert from 'node:assert/strict';

const API_URL = 'http://127.0.0.1:8000';

let isBackendAvailable = null;

async function checkBackend(t) {
  if (isBackendAvailable === null) {
    try {
      const res = await fetch(`${API_URL}/health`, { signal: AbortSignal.timeout(1000) });
      isBackendAvailable = res.ok;
    } catch {
      isBackendAvailable = false;
    }
  }
  if (!isBackendAvailable) {
    t.skip('FastAPI backend server is not running at ' + API_URL);
    return false;
  }
  return true;
}

test('Integration: FastAPI health probe returns status healthy', async (t) => {
  if (!await checkBackend(t)) return;
  const response = await fetch(`${API_URL}/health`);
  assert.equal(response.status, 200);
  const data = await response.json();
  assert.equal(data.status, 'healthy');
  assert.equal(data.application, 'FlowGrid');
});

test('Integration: Login failure with wrong credentials returns HTTP 401', async (t) => {
  if (!await checkBackend(t)) return;
  const response = await fetch(`${API_URL}/api/v1/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email: 'nonexistent@flowgrid.io',
      password: 'WrongPassword123!',
    }),
  });

  assert.equal(response.status, 401);
  const data = await response.json();
  assert.equal(data.detail, 'Invalid email or password');
});

test('Integration: Login success issues JWT access token and user profile', async (t) => {
  if (!await checkBackend(t)) return;
  const response = await fetch(`${API_URL}/api/v1/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email: 'manager@flowgrid.io',
      password: 'ManagerPass123!',
    }),
  });

  assert.equal(response.status, 200);
  const data = await response.json();
  assert.ok(data.access_token, 'Access token should be present');
  assert.equal(data.token_type, 'bearer');
  assert.ok(data.user, 'User profile should be present');
  assert.equal(data.user.email, 'manager@flowgrid.io');
  assert.equal(data.user.role, 'MANAGER');
});

test('Integration: GET /api/v1/auth/me succeeds with valid Bearer token', async (t) => {
  if (!await checkBackend(t)) return;
  // 1. Log in
  const loginRes = await fetch(`${API_URL}/api/v1/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email: 'manager@flowgrid.io',
      password: 'ManagerPass123!',
    }),
  });
  const loginData = await loginRes.json();
  const token = loginData.access_token;

  // 2. Fetch /me
  const meRes = await fetch(`${API_URL}/api/v1/auth/me`, {
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: 'application/json',
    },
  });

  assert.equal(meRes.status, 200);
  const meData = await meRes.json();
  assert.equal(meData.email, 'manager@flowgrid.io');
  assert.equal(meData.role, 'MANAGER');
  assert.equal(meData.is_active, true);
});

test('Integration: GET /api/v1/auth/me rejects invalid or missing token', async (t) => {
  if (!await checkBackend(t)) return;
  // Missing token
  const noTokenRes = await fetch(`${API_URL}/api/v1/auth/me`);
  assert.equal(noTokenRes.status, 401);

  // Invalid token
  const invalidTokenRes = await fetch(`${API_URL}/api/v1/auth/me`, {
    headers: { Authorization: 'Bearer invalid.jwt.signature' },
  });
  assert.equal(invalidTokenRes.status, 401);
});

test('Integration: User registration succeeds and prevents duplicates', async (t) => {
  if (!await checkBackend(t)) return;
  const timestamp = Date.now();
  const newEmail = `dispatch_op_${timestamp}@flowgrid.io`;

  // 1. Register new account
  const regRes = await fetch(`${API_URL}/api/v1/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name: 'Integration Operator',
      email: newEmail,
      password: 'SecurePassword123!',
      role: 'VIEWER',
    }),
  });

  assert.equal(regRes.status, 201);
  const regData = await regRes.json();
  assert.equal(regData.email, newEmail);
  assert.equal(regData.role, 'VIEWER');
  assert.equal(regData.is_active, true);

  // 2. Duplicate registration attempt fails
  const dupRes = await fetch(`${API_URL}/api/v1/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name: 'Integration Operator Duplicate',
      email: newEmail,
      password: 'SecurePassword123!',
      role: 'VIEWER',
    }),
  });

  assert.equal(dupRes.status, 400);
  const dupData = await dupRes.json();
  assert.match(dupData.detail, /already exists/i);
});

test('Integration: Registration rejects short password (< 6 chars)', async (t) => {
  if (!await checkBackend(t)) return;
  const badPassRes = await fetch(`${API_URL}/api/v1/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name: 'Bad Password User',
      email: `badpass_${Date.now()}@flowgrid.io`,
      password: '123',
      role: 'VIEWER',
    }),
  });

  assert.equal(badPassRes.status, 422);
});
