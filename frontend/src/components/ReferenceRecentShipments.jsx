import React from 'react';

/**
 * ReferenceRecentShipments
 * Displays the recent shipments table matching the reference image layout.
 * Columns: ID, Route, Status, ETA with "View all →" deep-link action.
 */
export default function ReferenceRecentShipments({ shipments = [], onNavigate, onSelectShipment }) {
  // Reference fallback items matching the demo design if backend has not loaded
  const fallbackShipments = [
    { id: 'FG-98421', route: 'Delhi → Mumbai', status: 'ON_TIME', eta: 'Apr 26, 10:30' },
    { id: 'FG-98422', route: 'Bengaluru → Chennai', status: 'DELAYED', eta: 'Apr 26, 18:45' },
    { id: 'FG-98423', route: 'Kolkata → Guwahati', status: 'ON_TIME', eta: 'Apr 27, 09:15' },
    { id: 'FG-98424', route: 'Hyderabad → Pune', status: 'ON_TIME', eta: 'Apr 27, 12:20' },
    { id: 'FG-98425', route: 'Mumbai → Delhi', status: 'AT_RISK', eta: 'Apr 27, 16:40' },
    { id: 'FG-98426', route: 'Chennai → Bengaluru', status: 'ON_TIME', eta: 'Apr 28, 08:10' },
  ];

  const displayList = shipments && shipments.length > 0
    ? shipments.slice(0, 6).map((s) => {
        const raw = s.raw || s;
        const origin = raw.origin_warehouse?.city || raw.origin_warehouse?.name || 'Hub A';
        const dest = raw.destination_warehouse?.city || raw.destination_warehouse?.name || 'Hub B';
        const routeStr = `${origin} → ${dest}`;
        
        let statusTag = 'ON_TIME';
        if (raw.status === 'FAILED' || raw.status === 'DELAYED') statusTag = 'DELAYED';
        else if (raw.status === 'CREATED' || raw.status === 'CANCELLED') statusTag = 'AT_RISK';
        
        const etaDate = raw.estimated_delivery
          ? new Date(raw.estimated_delivery).toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
          : 'Pending ETA';

        return {
          id: raw.tracking_number || `FG-${raw.id || '98400'}`,
          route: routeStr,
          status: statusTag,
          eta: etaDate,
          original: raw,
        };
      })
    : fallbackShipments;

  return (
    <div className="ref-recent-card" aria-label="Recent Line-Haul Shipments">
      <div className="ref-recent-header">
        <h2 className="ref-recent-title">Recent Shipments</h2>
        <button
          type="button"
          className="ref-view-all-link"
          onClick={() => onNavigate && onNavigate('shipments')}
        >
          View all →
        </button>
      </div>

      <div className="ref-table-wrapper">
        <table className="ref-shipments-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Route</th>
              <th>Status</th>
              <th>ETA</th>
            </tr>
          </thead>
          <tbody>
            {displayList.map((item, index) => {
              let badgeClass = 'badge-on-time';
              let badgeLabel = 'On Time';

              if (item.status === 'DELAYED') {
                badgeClass = 'badge-delayed';
                badgeLabel = 'Delayed';
              } else if (item.status === 'AT_RISK') {
                badgeClass = 'badge-at-risk';
                badgeLabel = 'At Risk';
              }

              return (
                <tr
                  key={item.id || index}
                  className="ref-shipment-row"
                  onClick={() => {
                    if (item.original && onSelectShipment) {
                      onSelectShipment(item.original);
                    } else if (onNavigate) {
                      onNavigate('shipments');
                    }
                  }}
                  title="Click to view full shipment details"
                >
                  <td className="cell-id">{item.id}</td>
                  <td className="cell-route">{item.route}</td>
                  <td className="cell-status">
                    <span className={`ref-status-badge ${badgeClass}`}>
                      {badgeLabel}
                    </span>
                  </td>
                  <td className="cell-eta">{item.eta}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
