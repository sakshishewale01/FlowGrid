import React from 'react';

export default function MetricCard({ metric }) {
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
