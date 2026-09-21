import React from 'react';
import { useAuth } from '../context/AuthContext';

/**
 * Reusable PageHeader component across all FlowGrid operations views.
 *
 * @param {Object} props
 * @param {string} props.section - Section category (e.g. 'OPERATIONS CONTROL / WAREHOUSES')
 * @param {string} props.title - Primary page heading (e.g. 'Warehouse Facilities')
 * @param {string} props.caption - Descriptive subtitle
 * @param {Array<{ label: string, value: string|number, status?: string }>} [props.metaPills] - Status pills
 * @param {Object} [props.primaryAction] - Optional action button config
 * @param {string} props.primaryAction.label - Button label
 * @param {Function} props.primaryAction.onClick - Button click handler
 * @param {string} [props.primaryAction.icon] - Optional icon
 * @param {Array<string>} [props.primaryAction.requiredRoles] - Roles allowed to perform action
 * @param {boolean} [props.primaryAction.loading] - Whether action is in loading state
 * @param {React.ReactNode} [props.children] - Additional header elements
 */
export default function PageHeader({
  section = 'OPERATIONS CONTROL',
  title,
  caption,
  metaPills = [],
  primaryAction = null,
  children,
}) {
  const { user } = useAuth();

  const isActionAllowed = !primaryAction?.requiredRoles || 
    primaryAction.requiredRoles.includes(user?.role);

  return (
    <div className="dashboard-header-bar page-header-bar">
      <div className="header-titles">
        <div className="breadcrumbs">{section}</div>
        <h1 className="dashboard-title">{title}</h1>
        {caption && <p className="dashboard-caption">{caption}</p>}
      </div>

      <div className="header-meta-group">
        {metaPills.map((pill, idx) => (
          <div key={idx} className="facility-status-pill">
            <span className={`indicator-dot ${pill.status || 'online'}`} />
            <span>
              {pill.label}: <strong>{pill.value}</strong>
            </span>
          </div>
        ))}

        {primaryAction && (
          <button
            type="button"
            className={`btn-action primary ${!isActionAllowed ? 'disabled' : ''}`}
            onClick={isActionAllowed ? primaryAction.onClick : undefined}
            disabled={primaryAction.loading || !isActionAllowed}
            title={!isActionAllowed ? `Action requires ${primaryAction.requiredRoles?.join(' or ')} role (Current: ${user?.role})` : primaryAction.label}
          >
            {primaryAction.icon || (
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <line x1="12" y1="5" x2="12" y2="19" />
                <line x1="5" y1="12" x2="19" y2="12" />
              </svg>
            )}
            <span>{primaryAction.label}</span>
            {!isActionAllowed && (
              <span className="role-lock-tag" title="Restricted by RBAC">🔒</span>
            )}
          </button>
        )}

        {children}
      </div>
    </div>
  );
}
