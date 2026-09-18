import React from 'react';

export default function WarehouseCards({ warehouses }) {
  return (
    <div className="warehouses-panel" id="warehouses-panel">
      <div className="panel-title-bar">
        <div>
          <h3 className="panel-title">Warehouse Facility Performance</h3>
          <p className="panel-subtitle">Capacity utilization, dock door activity, and daily throughput</p>
        </div>
        <button className="panel-action-link" id="btn-view-all-warehouses">
          Manage Hubs →
        </button>
      </div>

      <div className="warehouses-grid">
        {warehouses.map((wh) => {
          const isHighLoad = wh.capacityUsed >= 90;

          return (
            <div key={wh.id} className="warehouse-card" id={`wh-card-${wh.id}`}>
              <div className="wh-header">
                <div>
                  <span className="wh-code">{wh.id}</span>
                  <h4 className="wh-name">{wh.name}</h4>
                  <span className="wh-location">{wh.location}</span>
                </div>
                <span className={`wh-status-badge ${isHighLoad ? 'high-load' : 'optimal'}`}>
                  {wh.status}
                </span>
              </div>

              {/* Capacity Progress */}
              <div className="wh-capacity-section">
                <div className="capacity-label-row">
                  <span className="capacity-label">Storage Capacity</span>
                  <span className={`capacity-value ${isHighLoad ? 'alert' : ''}`}>
                    {wh.capacityUsed}%
                  </span>
                </div>
                <div className="capacity-track">
                  <div 
                    className={`capacity-fill ${isHighLoad ? 'high-load' : ''}`}
                    style={{ width: `${wh.capacityUsed}%` }}
                  />
                </div>
                <div className="wh-sqft">{wh.totalSqFt} total footprint</div>
              </div>

              {/* Operational Metrics */}
              <div className="wh-metrics-row">
                <div className="wh-metric-item">
                  <span className="item-label">Dock Bays</span>
                  <span className="item-val">{wh.activeBays}</span>
                </div>
                <div className="wh-metric-item">
                  <span className="item-label">Inbound (Today)</span>
                  <span className="item-val inbound">+{wh.inboundToday} trucks</span>
                </div>
                <div className="wh-metric-item">
                  <span className="item-label">Outbound (Today)</span>
                  <span className="item-val outbound">-{wh.outboundToday} trucks</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
