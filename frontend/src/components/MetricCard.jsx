import React from 'react';

export default function MetricCard({ metric, loading = false }) {
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

  return (
    <div className="metric-card" id={`metric-card-${metric.id}`}>
      <div className="metric-header">
        <span className="metric-label">{metric.label}</span>
        <div 
          className="metric-accent-dot" 
          style={{ backgroundColor: metric.accentColor }} 
        />
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
