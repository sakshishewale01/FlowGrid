import React from 'react';
import { useAuth } from '../context/AuthContext';

/**
 * Reusable EmptyState component.
 *
 * @param {Object} props
 * @param {string|React.ReactNode} [props.icon='📦']
 * @param {string} props.title
 * @param {string} [props.description]
 * @param {Object} [props.action]
 * @param {string} props.action.label
 * @param {Function} props.action.onClick
 * @param {Array<string>} [props.action.requiredRoles]
 */
export default function EmptyState({
  icon = '📦',
  title = 'No records found',
  description,
  action = null,
}) {
  const { user } = useAuth();
  const isActionAllowed = !action?.requiredRoles || action.requiredRoles.includes(user?.role);

  return (
    <div className="fg-empty-state-card">
      <div className="fg-empty-state-icon">
        {typeof icon === 'string' ? <span>{icon}</span> : icon}
      </div>
      <h3 className="fg-empty-state-title">{title}</h3>
      {description && <p className="fg-empty-state-desc">{description}</p>}
      {action && isActionAllowed && (
        <button
          type="button"
          className="btn-action primary"
          style={{ marginTop: '12px' }}
          onClick={action.onClick}
        >
          {action.label}
        </button>
      )}
    </div>
  );
}
