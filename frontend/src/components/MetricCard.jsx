import React from 'react';

export default function MetricCard({ metric, loading = false, onClick = null }) {
  if (loading || !metric) {
    return (
      <div className="metric-card skeleton-card">
        <div className="skeleton-line label" />
        <div className="skeleton-line value-large" />
        <div className="skeleton-line subtext" />
      </div>
    );
  }

  const isPositive = metric.changeType === 'positive';
  const isWarning = metric.changeType === 'warning';
  const isClickable = Boolean(onClick);

  const handleKeyDown = (e) => {
    if (isClickable && (e.key === 'Enter' || e.key === ' ')) {
      e.preventDefault();
      onClick();
    }
  };

  return (
    <div
      className={`metric-card ${isClickable ? 'metric-card-interactive' : ''}`}
      id={`metric-card-${metric.id}`}
      onClick={onClick}
      role={isClickable ? 'button' : undefined}
      tabIndex={isClickable ? 0 : undefined}
      onKeyDown={handleKeyDown}
      title={isClickable ? `Navigate to ${metric.label} records` : undefined}
      style={isClickable ? { cursor: 'pointer' } : undefined}
    >
      <div className="metric-header">
        <span className="metric-label">{metric.label}</span>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          {isClickable && (
            <svg
              className="metric-nav-arrow"
              width="12"
              height="12"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#64748B"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <polyline points="9 18 15 12 9 6" />
            </svg>
          )}
          <div
            className="metric-accent-dot"
            style={{ backgroundColor: metric.accentColor }}
          />
        </div>
      </div>

      <div className="metric-value-row">
        <span className="metric-value">{metric.value}</span>
      </div>

      <div className="metric-footer">
        <span className={`metric-change ${isPositive ? 'positive' : isWarning ? 'warning' : 'neutral'}`}>
          {isPositive ? '↑ ' : isWarning ? '⚠ ' : '• '}
          {metric.change}
        </span>
        <span className="metric-subtext">{metric.subtext}</span>
      </div>
    </div>
  );
}
