import React, { useState } from 'react';

export default function RecentShipmentsTable({ shipments = [], loading = false }) {
  const [filter, setFilter] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedShipment, setSelectedShipment] = useState(null);

  const filteredShipments = shipments.filter((item) => {
    const statusUpper = (item.status || '').toUpperCase();
    const matchesFilter = 
      filter === 'ALL' ||
      (filter === 'IN_TRANSIT' && (statusUpper === 'IN_TRANSIT' || statusUpper === 'OUT_FOR_DELIVERY' || statusUpper === 'PICKED_UP')) ||
      (filter === 'DELIVERED' && statusUpper === 'DELIVERED') ||
      (filter === 'ASSIGNED' && statusUpper === 'ASSIGNED') ||
      (filter === 'CONFIRMED' && statusUpper === 'CONFIRMED') ||
      (filter === 'FAILED' && (statusUpper === 'FAILED' || statusUpper === 'DELAYED' || statusUpper === 'RETURNED'));

    const searchLower = searchQuery.toLowerCase();
    const matchesSearch = 
      (item.trackingNumber || '').toLowerCase().includes(searchLower) ||
      (item.origin || '').toLowerCase().includes(searchLower) ||
      (item.destination || '').toLowerCase().includes(searchLower) ||
      (item.carrier || '').toLowerCase().includes(searchLower);

    return matchesFilter && matchesSearch;
  });

  const getStatusBadgeClass = (status) => {
    const s = (status || '').toUpperCase();
    switch (s) {
      case 'IN_TRANSIT':
      case 'OUT_FOR_DELIVERY':
      case 'PICKED_UP':
        return 'badge-transit';
      case 'DELIVERED':
        return 'badge-delivered';
      case 'DELAYED':
      case 'FAILED':
      case 'RETURNED':
        return 'badge-delayed';
      case 'ASSIGNED':
        return 'badge-assigned';
      case 'CONFIRMED':
        return 'badge-confirmed';
      default:
        return 'badge-default';
    }
  };

  return (
    <div className="table-panel" id="recent-shipments-panel">
      {/* Table Header & Controls */}
      <div className="table-controls-bar">
        <div>
          <h3 className="panel-title">Active Freight &amp; Recent Shipments</h3>
          <p className="panel-subtitle">Real-time status telemetry across registered line-haul shipments</p>
        </div>

        <div className="table-actions-right">
          {/* Status Filter Tabs */}
          <div className="filter-tabs-group" role="tablist">
            {['ALL', 'IN_TRANSIT', 'ASSIGNED', 'CONFIRMED', 'DELIVERED', 'FAILED'].map((tabKey) => (
              <button
                key={tabKey}
                className={`filter-tab-btn ${filter === tabKey ? 'active' : ''}`}
                onClick={() => setFilter(tabKey)}
              >
                {tabKey.replace('_', ' ')}
              </button>
            ))}
          </div>

          {/* Quick Filter Input */}
          <div className="table-search-box">
            <input
              type="text"
              placeholder="Search tracking, hub, driver..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="table-search-input"
              id="shipments-search-input"
            />
          </div>
        </div>
      </div>

      {/* Table Element */}
      <div className="table-responsive-wrapper">
        <table className="ops-table">
          <thead>
            <tr>
              <th>Tracking Number</th>
              <th>Origin Facility</th>
              <th>Destination</th>
              <th>Assigned Unit / Driver</th>
              <th>Cargo</th>
              <th>Status</th>
              <th>ETA</th>
              <th>Priority</th>
              <th style={{ textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              // Skeleton Loading Rows
              [1, 2, 3, 4, 5].map((rowIdx) => (
                <tr key={rowIdx} className="skeleton-row">
                  <td><div className="skeleton-line tracking" /></td>
                  <td><div className="skeleton-line text" /></td>
                  <td><div className="skeleton-line text" /></td>
                  <td><div className="skeleton-line text" /></td>
                  <td><div className="skeleton-line meta" /></td>
                  <td><div className="skeleton-line badge" /></td>
                  <td><div className="skeleton-line text" /></td>
                  <td><div className="skeleton-line pill" /></td>
                  <td><div className="skeleton-line btn" /></td>
                </tr>
              ))
            ) : filteredShipments.length === 0 ? (
              <tr>
                <td colSpan="9" className="empty-table-cell">
                  <div className="table-empty-container">
                    <span className="empty-icon">📦</span>
                    <span className="empty-title">
                      {shipments.length === 0
                        ? 'No shipments recorded in system yet'
                        : 'No shipments match the current filter criteria'}
                    </span>
                    <span className="empty-subtitle">
                      {shipments.length === 0
                        ? 'Create a new shipment order to initiate freight tracking.'
                        : 'Try adjusting your search query or selecting a different status filter.'}
                    </span>
                  </div>
                </td>
              </tr>
            ) : (
              filteredShipments.map((s) => (
                <tr key={s.trackingNumber} id={`row-${s.trackingNumber}`}>
                  <td>
                    <span className="tracking-code">{s.trackingNumber}</span>
                  </td>
                  <td className="facility-cell">{s.origin}</td>
                  <td className="facility-cell">{s.destination}</td>
                  <td>
                    <div className="carrier-name">{s.carrier}</div>
                  </td>
                  <td>
                    <div className="cargo-meta">{s.itemsCount} cbm • {s.weight}</div>
                  </td>
                  <td>
                    <span className={`status-badge ${getStatusBadgeClass(s.status)}`}>
                      <span className="badge-dot" />
                      {s.statusLabel}
                    </span>
                  </td>
                  <td>
                    <span className="eta-text">{s.eta}</span>
                  </td>
                  <td>
                    <span className={`priority-pill ${s.priority.toLowerCase().replace(/\s+/g, '-')}`}>
                      {s.priority}
                    </span>
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <button 
                      className="row-action-btn"
                      title="View Waybill & Manifest Details"
                      onClick={() => setSelectedShipment(s)}
                    >
                      Details
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="table-footer-bar">
        <span className="table-counter">
          Showing {filteredShipments.length} of {shipments.length} recorded shipments
        </span>
        <span className="table-sync-meta">Automated telematics sync active</span>
      </div>

      {/* Shipment Details Waybill Modal */}
      {selectedShipment && (
        <div className="modal-overlay" onClick={() => setSelectedShipment(null)}>
          <div className="waybill-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-title-group">
                <span className="modal-tag">FREIGHT WAYBILL MANIFEST</span>
                <h3 className="modal-title">{selectedShipment.trackingNumber}</h3>
              </div>
              <button 
                className="modal-close-btn" 
                onClick={() => setSelectedShipment(null)}
                aria-label="Close modal"
              >
                ×
              </button>
            </div>

            <div className="waybill-body">
              <div className="waybill-status-banner">
                <span className={`status-badge ${getStatusBadgeClass(selectedShipment.status)}`}>
                  <span className="badge-dot" />
                  {selectedShipment.statusLabel}
                </span>
                <span className="waybill-priority-tag">
                  Priority: <strong>{selectedShipment.priority}</strong>
                </span>
              </div>

              <div className="waybill-grid-2col">
                <div className="waybill-card">
                  <h4 className="waybill-card-title">Routing &amp; Facility</h4>
                  <div className="waybill-data-item">
                    <span className="data-key">Origin Hub:</span>
                    <span className="data-val">{selectedShipment.origin}</span>
                  </div>
                  <div className="waybill-data-item">
                    <span className="data-key">Destination:</span>
                    <span className="data-val">{selectedShipment.destination}</span>
                  </div>
                  <div className="waybill-data-item">
                    <span className="data-key">ETA / Delivery:</span>
                    <span className="data-val">{selectedShipment.eta}</span>
                  </div>
                </div>

                <div className="waybill-card">
                  <h4 className="waybill-card-title">Carrier &amp; Equipment</h4>
                  <div className="waybill-data-item">
                    <span className="data-key">Allocated Carrier:</span>
                    <span className="data-val">{selectedShipment.carrier}</span>
                  </div>
                  <div className="waybill-data-item">
                    <span className="data-key">Cargo Weight:</span>
                    <span className="data-val">{selectedShipment.weight}</span>
                  </div>
                  <div className="waybill-data-item">
                    <span className="data-key">Cargo Volume:</span>
                    <span className="data-val">{selectedShipment.itemsCount} cbm</span>
                  </div>
                </div>
              </div>

              {selectedShipment.raw && (
                <div className="waybill-audit-footer">
                  <span>Record ID: <code>#{selectedShipment.raw.id}</code></span>
                  <span>Created: <code>{new Date(selectedShipment.raw.created_at).toLocaleString()}</code></span>
                  <span>System State: <code>{selectedShipment.raw.status}</code></span>
                </div>
              )}
            </div>

            <div className="modal-footer">
              <button 
                className="auth-btn-primary" 
                onClick={() => setSelectedShipment(null)}
              >
                Close Waybill
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
