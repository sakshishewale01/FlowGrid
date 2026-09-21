import React from 'react';
import { useAuth } from '../context/AuthContext';

export default function QuickActions({ onAction }) {
  const { user, hasRole } = useAuth();

  const canManageShipments = hasRole(['ADMIN', 'MANAGER']);
  const canOptimizeRoutes = hasRole(['ADMIN', 'MANAGER']);

  return (
    <div className="quick-actions-bar" id="quick-actions-bar">
      <div className="actions-left">
        <span className="actions-label">QUICK DISPATCH:</span>

        {/* Primary Action Button: Requires ADMIN or MANAGER */}
        <button 
          className={`btn-action primary ${!canManageShipments ? 'btn-restricted' : ''}`}
          id="btn-quick-new-shipment"
          onClick={() => {
            if (canManageShipments) {
              onAction('Create New Shipment');
            } else {
              onAction('Action Denied: Creating shipments requires MANAGER or ADMIN role');
            }
          }}
          title={canManageShipments ? 'Create new freight shipment manifest' : `Restricted for role: ${user?.role || 'VIEWER'} (Requires MANAGER or ADMIN)`}
        >
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <line x1="12" y1="5" x2="12" y2="19"></line>
            <line x1="5" y1="12" x2="19" y2="12"></line>
          </svg>
          <span>New Shipment</span>
          {!canManageShipments && <span className="action-lock-icon">🔒</span>}
        </button>

        {/* Dispatch Route: Requires ADMIN or MANAGER */}
        <button 
          className={`btn-action secondary ${!canManageShipments ? 'btn-restricted' : ''}`}
          id="btn-quick-dispatch-route"
          onClick={() => {
            if (canManageShipments) {
              onAction('Dispatch Route');
            } else {
              onAction('Action Denied: Route dispatch requires MANAGER or ADMIN role');
            }
          }}
          title={canManageShipments ? 'Dispatch active transit route' : `Restricted for role: ${user?.role || 'VIEWER'} (Requires MANAGER or ADMIN)`}
        >
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polygon points="5 3 19 12 5 21 5 3"></polygon>
          </svg>
          <span>Dispatch Route</span>
          {!canManageShipments && <span className="action-lock-icon">🔒</span>}
        </button>

        {/* AI Optimization Action: Requires ADMIN or MANAGER */}
        <button 
          className={`btn-action ai-optimize ${!canOptimizeRoutes ? 'btn-restricted' : ''}`}
          id="btn-quick-ai-optimizer"
          onClick={() => {
            if (canOptimizeRoutes) {
              onAction('AI Route Optimization Algorithm');
            } else {
              onAction('Action Denied: AI corridor optimization requires MANAGER or ADMIN role');
            }
          }}
          title={canOptimizeRoutes ? 'scikit-learn dynamic routing optimization' : `Restricted for role: ${user?.role || 'VIEWER'} (Requires MANAGER or ADMIN)`}
        >
          <span className="ai-pill-tag">AI OPTIMIZE</span>
          <span>Dynamic Route Optimizer</span>
          {!canOptimizeRoutes && <span className="action-lock-icon">🔒</span>}
        </button>

        {/* Export Manifest: Available to all authenticated roles */}
        <button 
          className="btn-action outline"
          id="btn-quick-export-manifest"
          onClick={() => onAction('Export Manifest (PDF/CSV)')}
          title="Export operational manifest"
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
