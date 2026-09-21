import React, { useEffect } from 'react';
import { useAuth } from '../context/AuthContext';

/**
 * ProtectedRoute Component
 * ========================
 * Guards authenticated application routes:
 * 1. Shows a sleek loading screen while verifying JWT tokens on load/refresh.
 * 2. Redirects unauthenticated users to the Login view.
 * 3. Enforces optional role constraints.
 */
export default function ProtectedRoute({ 
  children, 
  allowedRoles, 
  onNavigate 
}) {

  const { isAuthenticated, isLoading, hasRole, user } = useAuth();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      if (onNavigate) {
        onNavigate('login');
      }
    }
  }, [isLoading, isAuthenticated, onNavigate]);

  // Loading state while restoring session from JWT
  if (isLoading) {
    return (
      <div className="auth-loading-screen" id="auth-loading-screen">
        <div className="auth-loading-spinner-box">
          <div className="auth-spinner-ring" />
          <div className="auth-loading-titles">
            <span className="auth-loading-brand">FLOWGRID</span>
            <span className="auth-loading-status">Verifying secure telemetry credentials...</span>
          </div>
        </div>
      </div>
    );
  }

  // Not authenticated: render nothing while redirect effect triggers
  if (!isAuthenticated) {
    return null;
  }

  // Role validation
  if (allowedRoles && !hasRole(allowedRoles)) {
    return (
      <div className="unauthorized-role-banner" id="unauthorized-role-banner">
        <div className="unauthorized-card">
          <div className="unauthorized-icon">🛡️</div>
          <h2>Restricted Operational Area</h2>
          <p>
            Your current role (<strong>{user?.role}</strong>) does not have authorization
            to access this view. Allowed roles: {Array.isArray(allowedRoles) ? allowedRoles.join(', ') : allowedRoles}.
          </p>
          <button 
            className="auth-btn-primary"
            onClick={() => onNavigate && onNavigate('dashboard')}
          >
            Return to Logistics Dashboard
          </button>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
