/**
 * FlowGrid Authentication Context
 * =================================
 * Manages global authentication state, token persistence, active session restoration,
 * role authorization helpers, and login/logout lifecycles.
 */

import React, { createContext, useState, useEffect, useCallback } from 'react';
import authApi from '../api/auth';

import {
  getStoredToken,
  setStoredToken,
  clearStoredToken,
} from '../api/client';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => getStoredToken());
  const [isLoading, setIsLoading] = useState(true);
  const [authError, setAuthError] = useState(null);

  /**
   * Restore user profile using the stored JWT token on app mount or refresh.
   */
  const restoreSession = useCallback(async () => {
    const storedToken = getStoredToken();
    if (!storedToken) {
      setUser(null);
      setToken(null);
      setIsLoading(false);
      return;
    }

    try {
      const userProfile = await authApi.getMe();
      setUser(userProfile);
      setToken(storedToken);
      setAuthError(null);
    } catch (err) {
      console.warn('Session restoration failed:', err.message);
      clearStoredToken();
      setUser(null);
      setToken(null);
      // Only set error if it wasn't a normal 401 expiration
      if (err.status !== 401) {
        setAuthError(err.message);
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    restoreSession();
  }, [restoreSession]);

  /**
   * Listen for global unauthorized events triggered by API client.
   */
  useEffect(() => {
    const handleUnauthorized = () => {
      console.info('Received 401 Unauthorized event. Logging out user.');
      clearStoredToken();
      setUser(null);
      setToken(null);
    };

    window.addEventListener('flowgrid:unauthorized', handleUnauthorized);
    return () => {
      window.removeEventListener('flowgrid:unauthorized', handleUnauthorized);
    };
  }, []);

  /**
   * Log in user with credentials, save token, and update auth state.
   */
  const login = async (email, password) => {
    setAuthError(null);
    try {
      const data = await authApi.login({ email, password });
      setStoredToken(data.access_token);
      setToken(data.access_token);

      let userProfile = data.user;
      if (!userProfile) {
        userProfile = await authApi.getMe();
      }
      setUser(userProfile);
      return { success: true, user: userProfile };
    } catch (err) {
      setAuthError(err.message);
      throw err;
    }
  };

  /**
   * Register a new user account.
   */
  const register = async ({ name, email, password, role = 'VIEWER' }) => {
    setAuthError(null);
    try {
      const createdUser = await authApi.register({ name, email, password, role });
      return { success: true, user: createdUser };
    } catch (err) {
      setAuthError(err.message);
      throw err;
    }
  };

  /**
   * Terminate active user session.
   */
  const logout = useCallback(() => {
    clearStoredToken();
    setUser(null);
    setToken(null);
    setAuthError(null);
  }, []);

  /**
   * Check if current user has one of the allowed roles.
   *
   * @param {string|string[]} allowedRoles - Role name or array of allowed roles
   * @returns {boolean}
   */
  const hasRole = useCallback(
    (allowedRoles) => {
      if (!user || !user.role) return false;
      if (Array.isArray(allowedRoles)) {
        return allowedRoles.includes(user.role);
      }
      return user.role === allowedRoles;
    },
    [user]
  );

  const clearError = () => setAuthError(null);

  const value = {
    user,
    token,
    isAuthenticated: Boolean(user && token),
    isLoading,
    authError,
    login,
    register,
    logout,
    restoreSession,
    hasRole,
    clearError,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export { useAuth } from './useAuth';
export default AuthContext;



