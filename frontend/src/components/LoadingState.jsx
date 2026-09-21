import React from 'react';

/**
 * Reusable LoadingState component for tables, panels, and full pages.
 *
 * @param {Object} props
 * @param {'spinner'|'skeleton-table'|'skeleton-card'} [props.variant='spinner']
 * @param {string} [props.message='Loading logistics telemetry...']
 * @param {number} [props.rows=4]
 * @param {number} [props.columns=6]
 */
export default function LoadingState({
  variant = 'spinner',
  message = 'Loading operational telemetry...',
  rows = 4,
  columns = 6,
}) {
  if (variant === 'skeleton-table') {
    return (
      <tbody className="fg-skeleton-tbody">
        {Array.from({ length: rows }).map((_, rIdx) => (
          <tr key={rIdx} className="skeleton-row">
            {Array.from({ length: columns }).map((_, cIdx) => (
              <td key={cIdx}>
                <div className="skeleton-line" style={{ width: cIdx === 0 ? '60%' : cIdx === 1 ? '85%' : '75%' }} />
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    );
  }

  if (variant === 'skeleton-card') {
    return (
      <div className="fg-skeleton-card-grid">
        {Array.from({ length: rows }).map((_, idx) => (
          <div key={idx} className="metric-card skeleton-card">
            <div className="skeleton-line title" style={{ width: '40%', height: '14px', marginBottom: '12px' }} />
            <div className="skeleton-line value" style={{ width: '65%', height: '28px', marginBottom: '10px' }} />
            <div className="skeleton-line subtitle" style={{ width: '80%', height: '12px' }} />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="fg-loading-container" role="status" aria-live="polite">
      <div className="fg-loading-spinner" />
      {message && <span className="fg-loading-message">{message}</span>}
    </div>
  );
}
