import React from 'react';

const STATUS_CONFIGS = {
  // Shipments
  CREATED: { label: 'Created', variant: 'neutral', dot: true },
  CONFIRMED: { label: 'Confirmed', variant: 'info', dot: true },
  ASSIGNED: { label: 'Assigned', variant: 'warning', dot: true },
  PICKED_UP: { label: 'Picked Up', variant: 'info', dot: true },
  IN_TRANSIT: { label: 'In Transit', variant: 'primary', dot: true },
  OUT_FOR_DELIVERY: { label: 'Out for Delivery', variant: 'primary', dot: true },
  DELIVERED: { label: 'Delivered', variant: 'success', dot: true },
  FAILED: { label: 'Failed', variant: 'danger', dot: true },
  RETURNED: { label: 'Returned', variant: 'danger', dot: true },
  CANCELLED: { label: 'Cancelled', variant: 'muted', dot: false },

  // Driver Availability
  AVAILABLE: { label: 'Available', variant: 'success', dot: true },
  ON_DUTY: { label: 'On Duty', variant: 'info', dot: true },
  OFF_DUTY: { label: 'Off Duty', variant: 'muted', dot: false },

  // Vehicle Status
  IN_USE: { label: 'In Service', variant: 'primary', dot: true },
  MAINTENANCE: { label: 'Maintenance', variant: 'warning', dot: true },
  DECOMMISSIONED: { label: 'Decommissioned', variant: 'danger', dot: false },

  // Warehouse / General
  OPERATIONAL: { label: 'Operational', variant: 'success', dot: true },
  ACTIVE: { label: 'Active', variant: 'success', dot: true },
  INACTIVE: { label: 'Inactive', variant: 'muted', dot: false },
  PLANNED: { label: 'Planned', variant: 'info', dot: true },
  COMPLETED: { label: 'Completed', variant: 'success', dot: true },

  // Inventory Health
  HEALTHY: { label: 'Healthy', variant: 'success', dot: true },
  LOW_STOCK: { label: 'Low Stock', variant: 'warning', dot: true },
  OUT_OF_STOCK: { label: 'Out of Stock', variant: 'danger', dot: true },
};

/**
 * Reusable StatusBadge component for consistent status tags across FlowGrid.
 *
 * @param {Object} props
 * @param {string} props.status - The raw status identifier (e.g. 'IN_TRANSIT', 'DELIVERED')
 * @param {string} [props.label] - Optional custom label
 * @param {'small'|'medium'|'large'} [props.size='medium']
 * @param {string} [props.className]
 */
export default function StatusBadge({ status, label, size = 'medium', className = '' }) {
  if (!status) return null;

  const normalized = String(status).toUpperCase();
  const config = STATUS_CONFIGS[normalized] || {
    label: status.replace(/_/g, ' '),
    variant: 'neutral',
    dot: true,
  };

  const displayLabel = label || config.label;

  return (
    <span className={`fg-status-badge fg-badge-${config.variant} fg-badge-${size} ${className}`}>
      {config.dot && <span className="fg-badge-dot" />}
      <span className="fg-badge-text">{displayLabel}</span>
    </span>
  );
}
