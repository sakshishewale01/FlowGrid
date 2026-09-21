import React from 'react';

/**
 * RoleBadge Component
 * ===================
 * Visual indicator tag reflecting user's role in the FlowGrid RBAC hierarchy:
 * - ADMIN: Purple/Indigo (Global access)
 * - MANAGER: Primary Blue (Operations & Dispatch)
 * - DRIVER: Cyan (Transit & Waypoints)
 * - VIEWER: Slate (Telemetry Observer)
 */
export default function RoleBadge({ role, size = 'normal', showDot = true }) {
  const normalizedRole = (role || 'VIEWER').toUpperCase();

  const roleConfigs = {
    ADMIN: {
      label: 'Admin',
      className: 'role-badge-admin',
      icon: '🛡️',
    },
    MANAGER: {
      label: 'Manager',
      className: 'role-badge-manager',
      icon: '⚡',
    },
    DRIVER: {
      label: 'Driver',
      className: 'role-badge-driver',
      icon: '🚚',
    },
    VIEWER: {
      label: 'Viewer',
      className: 'role-badge-viewer',
      icon: '👁️',
    },
  };

  const config = roleConfigs[normalizedRole] || roleConfigs.VIEWER;

  return (
    <span className={`role-badge ${config.className} role-badge-${size}`} title={`Role: ${normalizedRole}`}>
      {showDot && <span className="role-badge-dot" />}
      <span className="role-badge-text">{config.label}</span>
    </span>
  );
}
