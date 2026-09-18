import React from 'react';

export default function RouteMapPanel({ corridors }) {
  return (
    <div className="map-panel" id="route-map-panel">
      <div className="panel-title-bar">
        <div>
          <h3 className="panel-title">Freight Network &amp; Corridor Map</h3>
          <p className="panel-subtitle">Regional line-haul transit corridors with live telematics monitoring</p>
        </div>
        <div className="map-legend">
          <span className="legend-item"><span className="legend-dot normal" /> Clear Route</span>
          <span className="legend-item"><span className="legend-dot warning" /> Weather Alert</span>
        </div>
      </div>

      <div className="map-content-grid">
        {/* AI Route Optimization Callout - Uses Cyan #22D3EE sparingly */}
        <div className="ai-route-optimization-box" id="ai-optimization-banner">
          <div className="ai-opt-left">
            <span className="ai-sparkle-icon">✦</span>
            <span className="ai-opt-badge">AI OPTIMIZATION</span>
            <span>Dynamic Route Dispatcher active: <strong>+18.2% transit efficiency gain</strong></span>
          </div>
          <span className="ai-opt-stat">Active Predictive Model</span>
        </div>

        {/* Vector Schematic Map Canvas */}
        <div className="vector-map-canvas" id="network-schematic-canvas">
          <svg viewBox="0 0 700 320" className="schematic-svg" preserveAspectRatio="xMidYMid meet">
            {/* Grid Pattern */}
            <defs>
              <pattern id="grid-pattern" width="40" height="40" patternUnits="userSpaceOnUse">
                <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(255, 255, 255, 0.05)" strokeWidth="0.75" />
              </pattern>
            </defs>
            <rect width="700" height="320" fill="url(#grid-pattern)" />

            {/* Hub Interconnect Lines */}
            {/* ORD to EWR (Primary Blue #3B82F6) */}
            <path d="M 230 140 Q 380 90 550 120" fill="none" stroke="#3B82F6" strokeWidth="3" strokeDasharray="6,4" />
            
            {/* EWR to BOS (Weather Alert - Amber #F59E0B) */}
            <path d="M 550 120 Q 610 80 640 60" fill="none" stroke="#F59E0B" strokeWidth="3" />
            
            {/* DFW to ORD (Primary Blue #3B82F6) */}
            <path d="M 280 260 Q 250 200 230 140" fill="none" stroke="#3B82F6" strokeWidth="2.5" strokeDasharray="4,4" />
            
            {/* DFW to ATL (Secondary corridor) */}
            <path d="M 280 260 Q 380 240 460 210" fill="none" stroke="#475569" strokeWidth="2" strokeDasharray="2,2" />
            
            {/* ATL to EWR (Primary Blue #3B82F6) */}
            <path d="M 460 210 Q 510 160 550 120" fill="none" stroke="#3B82F6" strokeWidth="2.5" />

            {/* Hub Node: Chicago */}
            <g transform="translate(230, 140)">
              <circle r="16" fill="#3B82F6" fillOpacity="0.2" />
              <circle r="8" fill="#3B82F6" stroke="#0F172A" strokeWidth="2" />
              <text x="14" y="4" fontSize="12" fontWeight="600" fill="#E2E8F0">ORD (Chicago Hub)</text>
              <text x="14" y="18" fontSize="10" fill="#94A3B8">Central • 18 active</text>
            </g>

            {/* Hub Node: Newark */}
            <g transform="translate(550, 120)">
              <circle r="18" fill="#3B82F6" fillOpacity="0.2" />
              <circle r="9" fill="#3B82F6" stroke="#0F172A" strokeWidth="2" />
              <text x="-120" y="4" fontSize="12" fontWeight="600" fill="#E2E8F0">EWR (Newark Gateway)</text>
              <text x="-120" y="18" fontSize="10" fill="#94A3B8">East Coast • 24 active</text>
            </g>

            {/* Hub Node: Dallas */}
            <g transform="translate(280, 260)">
              <circle r="14" fill="#3B82F6" fillOpacity="0.2" />
              <circle r="7" fill="#3B82F6" stroke="#0F172A" strokeWidth="2" />
              <text x="12" y="4" fontSize="12" fontWeight="600" fill="#E2E8F0">DFW (Dallas Hub)</text>
              <text x="12" y="18" fontSize="10" fill="#94A3B8">Southwest • 12 active</text>
            </g>

            {/* Destination: Boston */}
            <g transform="translate(640, 60)">
              <circle r="6" fill="#F59E0B" stroke="#0F172A" strokeWidth="1.5" />
              <text x="-90" y="-8" fontSize="11" fontWeight="600" fill="#F59E0B">BOS (Boston)</text>
              <text x="-90" y="6" fontSize="9" fill="#94A3B8">Weather Hold</text>
            </g>

            {/* In-Transit Unit Marker on I-80 */}
            <g transform="translate(390, 110)">
              <rect x="-30" y="-12" width="60" height="24" rx="4" fill="#1E293B" stroke="#3B82F6" strokeWidth="1" />
              <text x="0" y="4" fontSize="10" fill="#38BDF8" fontWeight="600" textAnchor="middle">Unit #402</text>
            </g>
          </svg>
        </div>

        {/* Corridor Telematics Side List */}
        <div className="corridors-list">
          <div className="corridors-title">Key Freight Corridors</div>
          {corridors.map((corridor) => (
            <div key={corridor.id} className="corridor-card">
              <div className="corridor-header">
                <span className="corridor-name">{corridor.name}</span>
                <span className={`condition-pill ${corridor.statusType}`}>
                  {corridor.trafficCondition}
                </span>
              </div>
              <div className="corridor-stats">
                <span>Active Loads: <strong>{corridor.shipmentsActive}</strong></span>
                <span>Avg Speed: <strong>{corridor.avgSpeed}</strong></span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
