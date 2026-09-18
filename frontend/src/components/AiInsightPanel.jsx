import React from 'react';

export default function AiInsightPanel({ insights, onRunForecast }) {
  return (
    <div className="ai-insight-panel" id="ai-insight-panel">
      <div className="panel-title-bar">
        <div className="ai-title-wrapper">
          <div className="ai-icon-pulse">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#22D3EE" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
            </svg>
          </div>
          <div>
            <div className="ai-badge-row">
              <span className="ai-category-badge">INTELLIGENT LOGISTICS</span>
              <span className="ai-status-pill">ML Pipeline Ready</span>
            </div>
            <h3 className="panel-title">AI Predictive Intelligence &amp; Route Optimization</h3>
          </div>
        </div>

        <button 
          className="btn-ai-action"
          id="btn-trigger-ai-forecast"
          onClick={onRunForecast}
        >
          <span className="ai-sparkle">✦</span>
          <span>Run Forecast Simulation</span>
        </button>
      </div>

      <div className="ai-cards-grid">
        {insights.map((item) => (
          <div key={item.id} className="ai-card" id={`ai-card-${item.id}`}>
            <div className="ai-card-header">
              <span className="ai-card-category">{item.category}</span>
              <span className="ai-card-metric">{item.metric}</span>
            </div>
            <h4 className="ai-card-title">{item.title}</h4>
            <p className="ai-card-desc">{item.description}</p>
            <div className="ai-card-footer">
              <span className="ai-footer-dot" />
              <span className="ai-footer-status">{item.status}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
