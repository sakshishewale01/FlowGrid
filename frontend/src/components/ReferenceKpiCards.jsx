import React from 'react';

/**
 * ReferenceKpiCards matching the exact 4-card layout directly below the hero banner.
 * Features box, clock, alert triangle, and truck icons with clean typography and sparklines.
 */
export default function ReferenceKpiCards({ overview, delayRiskSummary, onNavigate }) {
  const totalShipments = overview?.total_shipments ? Number(overview.total_shipments).toLocaleString() : '1,248';
  const atRiskCount = delayRiskSummary?.high_risk_count ?? 48;
  const activeFleet = overview?.total_drivers ? (overview.total_drivers * 8 + 42) : '186';

  const cards = [
    {
      id: 'shipments',
      label: 'Total Shipments',
      value: totalShipments,
      trend: '↑ 12%',
      trendText: 'vs. last 7 days',
      trendClass: 'trend-success',
      iconType: 'box',
      iconBg: 'rgba(59, 130, 246, 0.16)',
      iconColor: '#38BDF8',
      sparklineColor: '#10B981',
      sparklinePath: 'M0,25 Q20,28 35,18 T70,22 T105,10 T140,5',
      route: 'shipments',
    },
    {
      id: 'on_time',
      label: 'On Time Delivery',
      value: '92.4%',
      trend: '↑ 3.2%',
      trendText: 'vs. last 7 days',
      trendClass: 'trend-cyan',
      iconType: 'clock',
      iconBg: 'rgba(34, 211, 238, 0.16)',
      iconColor: '#22D3EE',
      sparklineColor: '#22D3EE',
      sparklinePath: 'M0,22 Q25,26 45,15 T90,18 T120,12 T140,6',
      route: 'analytics',
    },
    {
      id: 'at_risk',
      label: 'At Risk Shipments',
      value: String(atRiskCount),
      trend: '↓ 18%',
      trendText: 'vs. last 7 days',
      trendClass: 'trend-warning',
      iconType: 'alert',
      iconBg: 'rgba(245, 158, 11, 0.16)',
      iconColor: '#F59E0B',
      sparklineColor: '#F59E0B',
      sparklinePath: 'M0,8 Q30,12 55,20 T95,15 T120,24 T140,26',
      route: 'rescue',
    },
    {
      id: 'active_fleet',
      label: 'Active Fleet',
      value: String(activeFleet),
      trend: '↑ 6%',
      trendText: 'vs. last 7 days',
      trendClass: 'trend-purple',
      iconType: 'truck',
      iconBg: 'rgba(168, 85, 247, 0.16)',
      iconColor: '#C084FC',
      sparklineColor: '#A855F7',
      sparklinePath: 'M0,26 Q25,20 50,24 T85,14 T115,16 T140,8',
      route: 'drivers',
    },
  ];

  return (
    <div className="ref-kpi-grid" aria-label="Key Operational Performance Indicators">
      {cards.map((card) => (
        <div
          key={card.id}
          className="ref-kpi-card"
          onClick={() => onNavigate && onNavigate(card.route)}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && onNavigate) onNavigate(card.route);
          }}
          title={`View ${card.label}`}
        >
          <div className="ref-kpi-top">
            <div className="ref-kpi-icon-box" style={{ backgroundColor: card.iconBg, color: card.iconColor }}>
              {card.iconType === 'box' && (
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
                  <polyline points="3.27 6.96 12 12.01 20.73 6.96" />
                  <line x1="12" y1="22.08" x2="12" y2="12" />
                </svg>
              )}
              {card.iconType === 'clock' && (
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10" />
                  <polyline points="12 6 12 12 16 14" />
                </svg>
              )}
              {card.iconType === 'alert' && (
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                  <line x1="12" y1="9" x2="12" y2="13" />
                  <line x1="12" y1="17" x2="12.01" y2="17" />
                </svg>
              )}
              {card.iconType === 'truck' && (
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="1" y="3" width="15" height="13" />
                  <polygon points="16 8 20 8 23 11 23 16 16 16 16 8" />
                  <circle cx="5.5" cy="18.5" r="2.5" />
                  <circle cx="18.5" cy="18.5" r="2.5" />
                </svg>
              )}
            </div>

            <div className="ref-kpi-header-text">
              <span className="ref-kpi-label">{card.label}</span>
              <span className="ref-kpi-val">{card.value}</span>
            </div>
          </div>

          <div className="ref-kpi-bottom">
            <div className="ref-kpi-trend-block">
              <span className={`ref-kpi-trend ${card.trendClass}`}>{card.trend}</span>
              <span className="ref-kpi-trend-caption">{card.trendText}</span>
            </div>
            <div className="ref-kpi-sparkline" aria-hidden="true">
              <svg width="100" height="32" viewBox="0 0 140 32" fill="none">
                <path
                  d={card.sparklinePath}
                  stroke={card.sparklineColor}
                  strokeWidth="2.2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
