import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';

export default function RegisterPage({ onNavigate }) {
  const { register, login } = useAuth();

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [role, setRole] = useState('VIEWER');
  const [showPassword, setShowPassword] = useState(false);

  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [validationErrors, setValidationErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Permitted self-registration roles (ADMIN is strictly excluded)
  const ALLOWED_ROLES = [
    {
      id: 'VIEWER',
      title: 'Viewer / Stakeholder',
      desc: 'Read-only freight telemetry, shipment lookups, and inventory dashboards.',
      badge: 'Read Only',
    },
    {
      id: 'MANAGER',
      title: 'Operations Dispatcher',
      desc: 'Create shipments, allocate warehouses, schedule drivers, and rebalance stock.',
      badge: 'Full Operations',
    },
    {
      id: 'DRIVER',
      title: 'Field Logistics Driver',
      desc: 'Access assigned freight routes, update transit status, and submit delivery proof.',
      badge: 'Field Mobile',
    },
  ];

  const validate = () => {
    const errors = {};
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (!name.trim()) {
      errors.name = 'Full name is required';
    } else if (name.trim().length < 2) {
      errors.name = 'Name must be at least 2 characters long';
    }

    if (!email.trim()) {
      errors.email = 'Corporate email address is required';
    } else if (!emailRegex.test(email.trim())) {
      errors.email = 'Please enter a valid email format';
    }

    if (!password) {
      errors.password = 'Password is required';
    } else if (password.length < 6) {
      errors.password = 'Password must be at least 6 characters long';
    }

    if (password !== confirmPassword) {
      errors.confirmPassword = 'Passwords do not match';
    }

    // Explicit security boundary: never allow self-registering as ADMIN
    if (role === 'ADMIN' || !['VIEWER', 'MANAGER', 'DRIVER'].includes(role)) {
      errors.role = 'ADMIN role cannot be self-registered. Please select a valid role.';
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');
    setSuccessMessage('');

    if (!validate()) {
      return;
    }

    setIsSubmitting(true);
    try {
      await register({
        name,
        email,
        password,
        role,
      });

      setSuccessMessage('Account created successfully! Signing in...');

      // Auto-login newly registered account for seamless onboarding
      try {
        await login(email, password);
        if (onNavigate) {
          setTimeout(() => {
            onNavigate('dashboard');
          }, 800);
        }
      } catch {
        // If auto-login fails, redirect to login page
        setTimeout(() => {
          if (onNavigate) onNavigate('login');
        }, 1500);
      }
    } catch (err) {
      setErrorMessage(err.message || 'Registration failed. Please check your details.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="auth-page-wrapper" id="flowgrid-register-view">
      {/* Background Accent Mesh */}
      <div className="auth-mesh-glow" />

      <div className="auth-container auth-container-wide">
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
            <span className="auth-brand-tag">PERSONNEL ONBOARDING</span>
          </div>
        </div>

        {/* Main Registration Card */}
        <div className="auth-card">
          <div className="auth-card-head">
            <h1 className="auth-title">Register Account</h1>
            <p className="auth-subtitle">
              Join the FlowGrid logistics network with your authorized operational profile.
            </p>
          </div>

          {/* Error Banner */}
          {errorMessage && (
            <div className="auth-alert error" role="alert" id="register-error-alert">
              <div className="auth-alert-icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10" />
                  <line x1="12" y1="8" x2="12" y2="12" />
                  <line x1="12" y1="16" x2="12.01" y2="16" />
                </svg>
              </div>
              <div className="auth-alert-content">
                <span className="auth-alert-title">Registration Error</span>
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

          {/* Success Banner */}
          {successMessage && (
            <div className="auth-alert success" role="alert" id="register-success-alert">
              <div className="auth-alert-icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                  <polyline points="22 4 12 14.01 9 11.01" />
                </svg>
              </div>
              <div className="auth-alert-content">
                <span className="auth-alert-title">Registration Completed</span>
                <span className="auth-alert-text">{successMessage}</span>
              </div>
            </div>
          )}

          {/* Registration Form */}
          <form className="auth-form" onSubmit={handleSubmit} noValidate>
            <div className="auth-grid-2col">
              {/* Full Name Field */}
              <div className={`auth-field ${validationErrors.name ? 'has-error' : ''}`}>
                <label htmlFor="reg-name" className="auth-label">
                  Full Name
                </label>
                <div className="auth-input-wrapper">
                  <span className="auth-input-icon">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                      <circle cx="12" cy="7" r="4" />
                    </svg>
                  </span>
                  <input
                    id="reg-name"
                    type="text"
                    className="auth-input"
                    placeholder="e.g. Sarah Jenkins"
                    value={name}
                    onChange={(e) => {
                      setName(e.target.value);
                      if (validationErrors.name) {
                        setValidationErrors((prev) => ({ ...prev, name: '' }));
                      }
                    }}
                    autoComplete="name"
                    required
                  />
                </div>
                {validationErrors.name && (
                  <span className="auth-field-error" id="name-error-msg">{validationErrors.name}</span>
                )}
              </div>

              {/* Corporate Email Field */}
              <div className={`auth-field ${validationErrors.email ? 'has-error' : ''}`}>
                <label htmlFor="reg-email" className="auth-label">
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
                    id="reg-email"
                    type="email"
                    className="auth-input"
                    placeholder="sarah.jenkins@flowgrid.io"
                    value={email}
                    onChange={(e) => {
                      setEmail(e.target.value);
                      if (validationErrors.email) {
                        setValidationErrors((prev) => ({ ...prev, email: '' }));
                      }
                    }}
                    autoComplete="email"
                    required
                  />
                </div>
                {validationErrors.email && (
                  <span className="auth-field-error" id="reg-email-error-msg">{validationErrors.email}</span>
                )}
              </div>
            </div>

            <div className="auth-grid-2col">
              {/* Password Field */}
              <div className={`auth-field ${validationErrors.password ? 'has-error' : ''}`}>
                <label htmlFor="reg-password" className="auth-label">
                  Password (Min 6 chars)
                </label>
                <div className="auth-input-wrapper">
                  <span className="auth-input-icon">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                      <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                    </svg>
                  </span>
                  <input
                    id="reg-password"
                    type={showPassword ? 'text' : 'password'}
                    className="auth-input"
                    placeholder="Create a strong password"
                    value={password}
                    onChange={(e) => {
                      setPassword(e.target.value);
                      if (validationErrors.password) {
                        setValidationErrors((prev) => ({ ...prev, password: '' }));
                      }
                    }}
                    autoComplete="new-password"
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
                  <span className="auth-field-error" id="reg-password-error-msg">{validationErrors.password}</span>
                )}
              </div>

              {/* Confirm Password Field */}
              <div className={`auth-field ${validationErrors.confirmPassword ? 'has-error' : ''}`}>
                <label htmlFor="reg-confirm-password" className="auth-label">
                  Confirm Password
                </label>
                <div className="auth-input-wrapper">
                  <span className="auth-input-icon">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                      <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                    </svg>
                  </span>
                  <input
                    id="reg-confirm-password"
                    type={showPassword ? 'text' : 'password'}
                    className="auth-input"
                    placeholder="Repeat password"
                    value={confirmPassword}
                    onChange={(e) => {
                      setConfirmPassword(e.target.value);
                      if (validationErrors.confirmPassword) {
                        setValidationErrors((prev) => ({ ...prev, confirmPassword: '' }));
                      }
                    }}
                    autoComplete="new-password"
                    required
                  />
                </div>
                {validationErrors.confirmPassword && (
                  <span className="auth-field-error" id="confirm-password-error-msg">{validationErrors.confirmPassword}</span>
                )}
              </div>
            </div>

            {/* Role Selection Group */}
            <div className="auth-field">
              <label className="auth-label">
                Operational Role Assignment
              </label>
              <div className="role-selector-grid">
                {ALLOWED_ROLES.map((r) => (
                  <label
                    key={r.id}
                    className={`role-choice-card ${role === r.id ? 'selected' : ''}`}
                  >
                    <input
                      type="radio"
                      name="operational-role"
                      value={r.id}
                      checked={role === r.id}
                      onChange={() => setRole(r.id)}
                      className="role-radio-hidden"
                    />
                    <div className="role-choice-header">
                      <span className="role-choice-title">{r.title}</span>
                      <span className="role-choice-badge">{r.badge}</span>
                    </div>
                    <p className="role-choice-desc">{r.desc}</p>
                  </label>
                ))}
              </div>

              {/* Security Boundary Alert */}
              <div className="auth-role-security-note">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10" />
                  <line x1="12" y1="16" x2="12" y2="12" />
                  <line x1="12" y1="8" x2="12.01" y2="8" />
                </svg>
                <span>
                  <strong>Security Policy:</strong> ADMIN privileges cannot be self-assigned and must be provisioned internally by platform administrators.
                </span>
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              className="auth-btn-primary"
              id="btn-register-submit"
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                <>
                  <span className="auth-spinner" />
                  <span>Provisioning Account...</span>
                </>
              ) : (
                <>
                  <span>Create Account</span>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <line x1="5" y1="12" x2="19" y2="12" />
                    <polyline points="12 5 19 12 12 19" />
                  </svg>
                </>
              )}
            </button>
          </form>

          {/* Card Footer: Switch to Login */}
          <div className="auth-card-footer">
            <span>Already have an operational account?</span>{' '}
            <button
              type="button"
              className="auth-link"
              id="link-go-to-login"
              onClick={() => onNavigate && onNavigate('login')}
            >
              Sign In
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
