import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';

export default function LoginPage({ onNavigate }) {
  const { login } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [validationErrors, setValidationErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Validate form fields before network call
  const validate = () => {
    const errors = {};
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (!email.trim()) {
      errors.email = 'Corporate email address is required';
    } else if (!emailRegex.test(email.trim())) {
      errors.email = 'Please enter a valid email address (e.g. user@flowgrid.io)';
    }

    if (!password) {
      errors.password = 'Password is required';
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');

    if (!validate()) {
      return;
    }

    setIsSubmitting(true);
    try {
      await login(email, password);
      // AuthContext will update user state; parent route navigates to dashboard
      if (onNavigate) {
        onNavigate('dashboard');
      }
    } catch (err) {
      setErrorMessage(err.message || 'Authentication failed. Please verify your credentials.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Demo credential autofill helper
  const handleQuickFill = (demoEmail, demoPassword) => {
    setEmail(demoEmail);
    setPassword(demoPassword);
    setValidationErrors({});
    setErrorMessage('');
  };

  return (
    <div className="auth-page-wrapper" id="flowgrid-login-view">
      {/* Background Accent Mesh */}
      <div className="auth-mesh-glow" />

      <div className="auth-container">
        {/* Brand Card Header */}
        <div className="auth-brand-header">
          <div className="auth-brand-badge">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="2" y="7" width="20" height="14" rx="2" ry="2" />
              <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" />
            </svg>
          </div>
          <div className="auth-brand-titles">
            <span className="auth-brand-name">FLOWGRID</span>
            <span className="auth-brand-tag">LOGISTICS CONTROL CENTER</span>
          </div>
        </div>

        {/* Main Authentication Box */}
        <div className="auth-card">
          <div className="auth-card-head">
            <h1 className="auth-title">Operational Access</h1>
            <p className="auth-subtitle">
              Sign in with your FlowGrid credentials to access telemetry, route optimization, and multi-hub dispatch.
            </p>
          </div>

          {/* Error Banner */}
          {errorMessage && (
            <div className="auth-alert error" role="alert" id="auth-error-alert">
              <div className="auth-alert-icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10" />
                  <line x1="12" y1="8" x2="12" y2="12" />
                  <line x1="12" y1="16" x2="12.01" y2="16" />
                </svg>
              </div>
              <div className="auth-alert-content">
                <span className="auth-alert-title">Authentication Failed</span>
                <span className="auth-alert-text">{errorMessage}</span>
              </div>
              <button
                type="button"
                className="auth-alert-close"
                onClick={() => setErrorMessage('')}
                aria-label="Dismiss alert"
              >
                ×
              </button>
            </div>
          )}

          {/* Login Form */}
          <form className="auth-form" onSubmit={handleSubmit} noValidate>
            {/* Email Field */}
            <div className={`auth-field ${validationErrors.email ? 'has-error' : ''}`}>
              <label htmlFor="login-email" className="auth-label">
                Corporate Email
              </label>
              <div className="auth-input-wrapper">
                <span className="auth-input-icon">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
                    <polyline points="22,6 12,13 2,6" />
                  </svg>
                </span>
                <input
                  id="login-email"
                  type="email"
                  className="auth-input"
                  placeholder="name@flowgrid.io"
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value);
                    if (validationErrors.email) {
                      setValidationErrors((prev) => ({ ...prev, email: '' }));
                    }
                  }}
                  autoComplete="username"
                  required
                />
              </div>
              {validationErrors.email && (
                <span className="auth-field-error" id="email-error-msg">{validationErrors.email}</span>
              )}
            </div>

            {/* Password Field */}
            <div className={`auth-field ${validationErrors.password ? 'has-error' : ''}`}>
              <div className="auth-label-row">
                <label htmlFor="login-password" className="auth-label">
                  Password
                </label>
              </div>
              <div className="auth-input-wrapper">
                <span className="auth-input-icon">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                    <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                  </svg>
                </span>
                <input
                  id="login-password"
                  type={showPassword ? 'text' : 'password'}
                  className="auth-input"
                  placeholder="Enter security password"
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                    if (validationErrors.password) {
                      setValidationErrors((prev) => ({ ...prev, password: '' }));
                    }
                  }}
                  autoComplete="current-password"
                  required
                />
                <button
                  type="button"
                  className="auth-toggle-pwd"
                  onClick={() => setShowPassword(!showPassword)}
                  tabIndex={-1}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? (
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
                      <line x1="1" y1="1" x2="23" y2="23" />
                    </svg>
                  ) : (
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                      <circle cx="12" cy="12" r="3" />
                    </svg>
                  )}
                </button>
              </div>
              {validationErrors.password && (
                <span className="auth-field-error" id="password-error-msg">{validationErrors.password}</span>
              )}
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              className="auth-btn-primary"
              id="btn-login-submit"
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                <>
                  <span className="auth-spinner" />
                  <span>Authenticating Dispatcher...</span>
                </>
              ) : (
                <>
                  <span>Sign In to Control Center</span>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <line x1="5" y1="12" x2="19" y2="12" />
                    <polyline points="12 5 19 12 12 19" />
                  </svg>
                </>
              )}
            </button>
          </form>

          {/* Quick Fill / Demo Accounts Section */}
          <div className="auth-demo-section">
            <div className="auth-demo-header">
              <span className="auth-demo-divider" />
              <span className="auth-demo-title">DEMO OPERATIONAL ACCOUNTS</span>
              <span className="auth-demo-divider" />
            </div>
            <div className="auth-demo-chips">
              <button
                type="button"
                className="demo-chip chip-manager"
                onClick={() => handleQuickFill('manager@flowgrid.io', 'ManagerPass123!')}
                title="Log in as Warehouse Operations Dispatcher"
              >
                <span className="demo-chip-role">Manager</span>
                <span className="demo-chip-email">manager@flowgrid.io</span>
              </button>
              <button
                type="button"
                className="demo-chip chip-driver"
                onClick={() => handleQuickFill('driver@flowgrid.io', 'DriverPass123!')}
                title="Log in as Field Logistics Driver"
              >
                <span className="demo-chip-role">Driver</span>
                <span className="demo-chip-email">driver@flowgrid.io</span>
              </button>
              <button
                type="button"
                className="demo-chip chip-viewer"
                onClick={() => handleQuickFill('viewer@flowgrid.io', 'ViewerPass123!')}
                title="Log in as Read-Only Stakeholder"
              >
                <span className="demo-chip-role">Viewer</span>
                <span className="demo-chip-email">viewer@flowgrid.io</span>
              </button>
              <button
                type="button"
                className="demo-chip chip-admin"
                onClick={() => handleQuickFill('admin@flowgrid.io', 'AdminPass123!')}
                title="Log in as System Administrator"
              >
                <span className="demo-chip-role">Admin</span>
                <span className="demo-chip-email">admin@flowgrid.io</span>
              </button>
            </div>
          </div>

          {/* Card Footer: Link to Register */}
          <div className="auth-card-footer">
            <span>New to the FlowGrid Network?</span>{' '}
            <button
              type="button"
              className="auth-link"
              id="link-go-to-register"
              onClick={() => onNavigate && onNavigate('register')}
            >
              Create Account
            </button>
          </div>
        </div>

        {/* Security Hardening Note */}
        <div className="auth-security-footer">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
            <path d="M7 11V7a5 5 0 0 1 10 0v4" />
          </svg>
          <span>Argon2id Password Hashing • HMAC-SHA256 Signed JWT Telemetry</span>
        </div>
      </div>
    </div>
  );
}
