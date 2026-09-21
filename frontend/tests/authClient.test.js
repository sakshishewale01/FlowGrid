import test from 'node:test';
import assert from 'node:assert/strict';
import {
  formatErrorMessage,
  ApiError,
  getApiBaseUrl,
  TOKEN_STORAGE_KEY,
} from '../src/api/client.js';

test('formatErrorMessage handles string detail', () => {
  const data = { detail: 'Invalid email or password' };
  const message = formatErrorMessage(data);
  assert.equal(message, 'Invalid email or password');
});

test('formatErrorMessage handles FastAPI Pydantic 422 array of validation errors', () => {
  const data = {
    detail: [
      { loc: ['body', 'email'], msg: 'value is not a valid email address', type: 'value_error' },
      { loc: ['body', 'password'], msg: 'String should have at least 6 characters', type: 'string_too_short' }
    ]
  };
  const message = formatErrorMessage(data);
  assert.equal(message, 'email: value is not a valid email address; password: String should have at least 6 characters');
});

test('formatErrorMessage falls back to default message when payload is empty or invalid', () => {
  assert.equal(formatErrorMessage(null, 'Custom fallback'), 'Custom fallback');
  assert.equal(formatErrorMessage({}, 'Default error'), 'Default error');
});

test('ApiError captures status code, message, and data payload', () => {
  const err = new ApiError('Unauthorized Access', 401, { detail: 'Token expired' });
  assert.equal(err.name, 'ApiError');
  assert.equal(err.status, 401);
  assert.equal(err.message, 'Unauthorized Access');
  assert.deepEqual(err.data, { detail: 'Token expired' });
});

test('getApiBaseUrl returns configured base URL or default 127.0.0.1:8000', () => {
  const url = getApiBaseUrl();
  assert.ok(url.startsWith('http://') || url.startsWith('https://'));
  assert.equal(url.endsWith('/'), false);
});

test('TOKEN_STORAGE_KEY constant is flowgrid_access_token', () => {
  assert.equal(TOKEN_STORAGE_KEY, 'flowgrid_access_token');
});
