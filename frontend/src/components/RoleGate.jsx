import React from 'react';
import { useAuth } from '../context/AuthContext';

/**
 * RoleGate Component
 * ==================
 * Declarative component for UI authorization. Renders children only if
 * current user's role matches one of the `allowedRoles`.
 *
 * NOTE: Frontend role checks protect UX presentation; FastAPI backend
 * dependencies (require_roles) enforce the real security boundary.
 *
 * @param {string|string[]} allowedRoles - Single role or array of allowed roles
 * @param {React.ReactNode} [fallback=null] - Optional element to render when unauthorized
 * @param {React.ReactNode} children - Protected UI elements
 */
export default function RoleGate({ allowedRoles, fallback = null, children }) {
  const { hasRole, isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return fallback;
  }

  if (hasRole(allowedRoles)) {
    return <>{children}</>;
  }

  return fallback;
}
