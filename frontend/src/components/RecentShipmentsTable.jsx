import React, { useState } from 'react';

export default function RecentShipmentsTable({ shipments }) {
  const [filter, setFilter] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  const filteredShipments = shipments.filter((item) => {
    const matchesFilter = 
      filter === 'ALL' ||
      (filter === 'IN_TRANSIT' && (item.status === 'IN_TRANSIT' || item.status === 'OUT_FOR_DELIVERY')) ||
      (filter === 'DELIVERED' && item.status === 'DELIVERED') ||
      (filter === 'DELAYED' && item.status === 'DELAYED');

    const matchesSearch = 
      item.trackingNumber.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.origin.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.destination.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.carrier.toLowerCase().includes(searchQuery.toLowerCase());

    return matchesFilter && matchesSearch;
  });

  const getStatusBadgeClass = (status) => {
    switch (status) {
      case 'IN_TRANSIT':
      case 'OUT_FOR_DELIVERY':
        return 'badge-transit';
      case 'DELIVERED':
        return 'badge-delivered';
      case 'DELAYED':
        return 'badge-delayed';
      case 'ASSIGNED':
        return 'badge-assigned';
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
          <p className="panel-subtitle">Real-time status updates across all active line-haul movements</p>
        </div>

        <div className="table-actions-right">
          {/* Status Filter Tabs */}
          <div className="filter-tabs-group" role="tablist">
            {['ALL', 'IN_TRANSIT', 'DELIVERED', 'DELAYED'].map((tabKey) => (
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
              placeholder="Filter shipments..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="table-search-input"
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
            {filteredShipments.map((s) => (
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
                  <div className="cargo-meta">{s.itemsCount} units • {s.weight}</div>
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
                  <span className={`priority-pill ${s.priority.toLowerCase()}`}>
                    {s.priority}
                  </span>
                </td>
                <td style={{ textAlign: 'right' }}>
                  <button 
                    className="row-action-btn"
                    title="View Waybill & Manifest"
                    onClick={() => alert(`Viewing shipment details for ${s.trackingNumber}`)}
                  >
                    Details
                  </button>
                </td>
              </tr>
            ))}
            {filteredShipments.length === 0 && (
              <tr>
                <td colSpan="9" className="empty-table-cell">
                  No shipments found matching the selected filter criteria.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="table-footer-bar">
        <span className="table-counter">
          Showing {filteredShipments.length} of {shipments.length} loaded shipments
        </span>
        <span className="table-sync-meta">Automated telematics sync active</span>
      </div>
    </div>
  );
}
