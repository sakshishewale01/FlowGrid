import React from 'react';

export default function WarehouseCards({ warehouses = [], loading = false, inventorySummary = null }) {
  return (
    <div className="warehouses-panel" id="warehouses-panel">
      <div className="panel-title-bar">
        <div>
          <h3 className="panel-title">Warehouse Facility Performance</h3>
          <p className="panel-subtitle">
            Capacity utilization, on-hand inventory levels, and facility throughput
          </p>
        </div>
        <div className="panel-header-badges">
          {inventorySummary && (
            <span className="inventory-stat-chip" title="Total inventory on hand across network">
              Stock: <strong>{Number(inventorySummary.totalQuantity).toLocaleString()} units</strong>
            </span>
          )}
          {inventorySummary?.lowStockCount > 0 && (
            <span className="inventory-alert-chip" title="Items below safety threshold">
              ⚠️ {inventorySummary.lowStockCount} Low Stock
            </span>
          )}
        </div>
      </div>

      {loading ? (
        <div className="warehouses-grid">
          {[1, 2, 3].map((idx) => (
            <div key={idx} className="warehouse-card skeleton-card">
              <div className="skeleton-line title" />
              <div className="skeleton-line subtitle" />
              <div className="skeleton-bar" />
              <div className="skeleton-line details" />
            </div>
          ))}
        </div>
      ) : warehouses.length === 0 ? (
        <div className="panel-empty-state" id="warehouses-empty-state">
          <div className="empty-icon">🏢</div>
          <h4 className="empty-title">No Warehouse Facilities Found</h4>
          <p className="empty-desc">
            No warehouse hubs are currently registered in the database. When facilities are provisioned, their capacity and inventory will appear here.
          </p>
        </div>
      ) : (
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
                  <span className={`wh-status-badge ${isHighLoad ? 'high-load' : wh.status === 'Attention' ? 'attention' : 'optimal'}`}>
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
                      style={{ width: `${Math.max(5, Math.min(100, wh.capacityUsed))}%` }}
                    />
                  </div>
                  <div className="wh-sqft">{wh.totalSqFt} total footprint</div>
                </div>

                {/* Operational Metrics */}
                <div className="wh-metrics-row">
                  <div className="wh-metric-item">
                    <span className="item-label">Product Lines</span>
                    <span className="item-val">{wh.activeBays}</span>
                  </div>
                  <div className="wh-metric-item">
                    <span className="item-label">On-Hand Stock</span>
                    <span className="item-val inbound">
                      {typeof wh.inboundToday === 'number'
                        ? `${Number(wh.inboundToday).toLocaleString()} units`
                        : wh.inboundToday}
                    </span>
                  </div>
                  <div className="wh-metric-item">
                    <span className="item-label">Low Stock Alerts</span>
                    <span className={`item-val ${wh.outboundToday > 0 ? 'alert-warning' : 'outbound'}`}>
                      {wh.outboundToday} items
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
