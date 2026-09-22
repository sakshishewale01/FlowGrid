/**
 * FlowGrid Centralized API Client
 * =================================
 * Provides authenticated, type-safe HTTP communication with the FastAPI backend.
 *
 * Core Features:
 * - Environment-configured base URL (VITE_API_BASE_URL).
 * - Automatic Bearer token header injection from localStorage.
 * - Centralized response parsing and FastAPI error decoding (strings & Pydantic 422 lists).
 * - Automatic 401 Unauthorized event dispatch for graceful session expiration.
 * - Comprehensive offline/network error trapping.
 */

// Centralized Token Storage Key
export const TOKEN_STORAGE_KEY = 'flowgrid_access_token';

// Determine backend API Base URL
export const getApiBaseUrl = () => {
  const envUrl = typeof import.meta !== 'undefined' && import.meta.env
    ? import.meta.env.VITE_API_BASE_URL
    : undefined;

  if (envUrl && envUrl.trim() !== '') {
    return envUrl.replace(/\/+$/, '');
  }
  // Default to local FastAPI backend
  return 'http://127.0.0.1:8000';
};

export const API_BASE_URL = getApiBaseUrl();

/**
 * Determine WebSocket Base URL derived from API base URL (ws:// or wss://).
 */
export const getWsBaseUrl = () => {
  const httpUrl = getApiBaseUrl();
  return httpUrl.replace(/^http/, 'ws');
};


/**
 * Retrieve the stored JWT token from localStorage.
 */
export const getStoredToken = () => {
  try {
    return localStorage.getItem(TOKEN_STORAGE_KEY);
  } catch (err) {
    console.warn('Unable to access localStorage for auth token:', err);
    return null;
  }
};

/**
 * Persist a newly issued JWT token into localStorage.
 */
export const setStoredToken = (token) => {
  try {
    if (token) {
      localStorage.setItem(TOKEN_STORAGE_KEY, token);
    } else {
      localStorage.removeItem(TOKEN_STORAGE_KEY);
    }
  } catch (err) {
    console.warn('Unable to persist auth token to localStorage:', err);
  }
};

/**
 * Clear the stored JWT token from localStorage.
 */
export const clearStoredToken = () => {
  try {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
  } catch (err) {
    console.warn('Unable to remove auth token from localStorage:', err);
  }
};

/**
 * Custom error class capturing HTTP status code and server payload.
 */
export class ApiError extends Error {
  constructor(message, status, data = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

/**
 * Formats FastAPI error responses into human-readable messages.
 * Handles both string details and Pydantic validation error arrays.
 */
export const formatErrorMessage = (data, fallbackMessage = 'An unexpected API error occurred') => {
  if (!data) return fallbackMessage;

  if (typeof data.detail === 'string') {
    return data.detail;
  }

  if (Array.isArray(data.detail)) {
    return data.detail
      .map((item) => {
        const field = Array.isArray(item.loc) ? item.loc.filter((p) => p !== 'body').join('.') : '';
        return field ? `${field}: ${item.msg}` : item.msg;
      })
      .filter(Boolean)
      .join('; ');
  }

  if (data.message && typeof data.message === 'string') {
    return data.message;
  }

  return fallbackMessage;
};

/**
 * Execute an HTTP request against the FlowGrid API.
 *
 * @param {string} endpoint - Relative path (e.g. '/api/v1/auth/login') or absolute URL.
 * @param {RequestInit & { body?: any }} options - Standard fetch options.
 * @returns {Promise<any>} Parsed response data.
 */
export async function apiFetch(endpoint, options = {}) {
  const baseUrl = getApiBaseUrl();
  const url = endpoint.startsWith('http://') || endpoint.startsWith('https://')
    ? endpoint
    : `${baseUrl}${endpoint.startsWith('/') ? '' : '/'}${endpoint}`;

  const headers = new Headers(options.headers || {});

  // Set default Accept header
  if (!headers.has('Accept')) {
    headers.set('Accept', 'application/json');
  }

  // Automatically attach Bearer token if present and not explicitly provided
  const token = getStoredToken();
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  let body = options.body;
  if (body && typeof body === 'object' && !(body instanceof FormData) && !(body instanceof Blob) && !(body instanceof URLSearchParams)) {
    if (!headers.has('Content-Type')) {
      headers.set('Content-Type', 'application/json');
    }
    body = JSON.stringify(body);
  }

  const fetchConfig = {
    ...options,
    headers,
    body,
  };

  let response;
  try {
    response = await fetch(url, fetchConfig);
  } catch (networkError) {
    const errorMsg = `Unable to connect to FlowGrid API at ${baseUrl}. Ensure backend is running.`;
    throw new ApiError(errorMsg, 0, { networkError: networkError.message });
  }

  // Parse response body
  let data = null;
  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    try {
      data = await response.json();
    } catch {
      data = null;
    }
  } else {
    try {
      data = await response.text();
    } catch {
      data = null;
    }
  }

  // Handle unauthorized responses
  if (response.status === 401) {
    if (typeof window !== 'undefined') {
      window.dispatchEvent(
        new CustomEvent('flowgrid:unauthorized', {
          detail: { status: 401, endpoint, data },
        })
      );
    }
  }

  if (!response.ok) {
    const defaultMsg = `Request failed with status ${response.status} (${response.statusText || 'Error'})`;
    const message = formatErrorMessage(data, defaultMsg);
    throw new ApiError(message, response.status, data);
  }

  return data;
}

// Convenient HTTP methods
export const apiClient = {
  get: (endpoint, options = {}) => apiFetch(endpoint, { ...options, method: 'GET' }),
  post: (endpoint, body, options = {}) => apiFetch(endpoint, { ...options, method: 'POST', body }),
  put: (endpoint, body, options = {}) => apiFetch(endpoint, { ...options, method: 'PUT', body }),
  patch: (endpoint, body, options = {}) => apiFetch(endpoint, { ...options, method: 'PATCH', body }),
  delete: (endpoint, options = {}) => apiFetch(endpoint, { ...options, method: 'DELETE' }),
};

export default apiClient;
