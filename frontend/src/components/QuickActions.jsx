import React from 'react';

export default function QuickActions({ onAction }) {
  return (
    <div className="quick-actions-bar" id="quick-actions-bar">
      <div className="actions-left">
        <span className="actions-label">QUICK DISPATCH:</span>

        {/* Primary Action Button in Blue #3B82F6 */}
        <button 
          className="btn-action primary"
          id="btn-quick-new-shipment"
          onClick={() => onAction('Create New Shipment')}
        >
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <line x1="12" y1="5" x2="12" y2="19"></line>
            <line x1="5" y1="12" x2="19" y2="12"></line>
          </svg>
          New Shipment
        </button>

        {/* Standard Operational Button */}
        <button 
          className="btn-action secondary"
          id="btn-quick-dispatch-route"
          onClick={() => onAction('Dispatch Route')}
        >
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polygon points="5 3 19 12 5 21 5 3"></polygon>
          </svg>
          Dispatch Route
        </button>

        {/* AI & Optimization Action (Uses Cyan #22D3EE sparingly) */}
        <button 
          className="btn-action ai-optimize"
          id="btn-quick-ai-optimizer"
          onClick={() => onAction('AI Route Optimization Algorithm')}
          title="scikit-learn dynamic routing optimization"
        >
          <span className="ai-pill-tag">AI OPTIMIZE</span>
          <span>Dynamic Route Optimizer</span>
        </button>

        {/* Export Manifest */}
        <button 
          className="btn-action outline"
          id="btn-quick-export-manifest"
          onClick={() => onAction('Export Manifest (PDF/CSV)')}
        >
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="7 10 12 15 17 10"></polyline>
            <line x1="12" y1="15" x2="12" y2="3"></line>
          </svg>
          Export Manifest
        </button>
      </div>

      <div className="actions-right">
        <span className="telematics-status">
          <span className="telematics-pulse" />
          Telematics Link: <strong>Active (2.4s sync)</strong>
        </span>
      </div>
    </div>
  );
}
