import React, { useState } from 'react';

/**
 * LiveShipmentFlowMap
 * Interactive freight corridor network visualization matching the reference image.
 * Displays key logistics hubs (Delhi, Mumbai, Kolkata, Hyderabad, Bengaluru) with
 * animated transit flows, status markers, interactive tooltips, and floating active manifest pill.
 */
export default function LiveShipmentFlowMap({ onNavigate }) {
  const [activeCity, setActiveCity] = useState(null);
  const [zoomLevel, setZoomLevel] = useState(1);

  const hubs = [
    { id: 'delhi', name: 'Delhi', x: 200, y: 70, status: 'IN_TRANSIT', color: '#38BDF8', activeLoads: 342 },
    { id: 'mumbai', name: 'Mumbai', x: 120, y: 195, status: 'DELIVERED', color: '#10B981', activeLoads: 288 },
    { id: 'hyderabad', name: 'Hyderabad', x: 215, y: 240, status: 'HIGH_RISK', color: '#22D3EE', activeLoads: 195 },
    { id: 'kolkata', name: 'Kolkata', x: 320, y: 145, status: 'DELAYED', color: '#F43F5E', activeLoads: 174 },
    { id: 'bengaluru', name: 'Bengaluru', x: 195, y: 310, status: 'IN_TRANSIT', color: '#38BDF8', activeLoads: 249 },
  ];

  const routes = [
    { id: 'delhi-mumbai', from: [200, 70], to: [120, 195], color: '#38BDF8', strokeDash: '4,4' },
    { id: 'delhi-kolkata', from: [200, 70], to: [320, 145], color: '#38BDF8', strokeDash: '4,4' },
    { id: 'mumbai-hyderabad', from: [120, 195], to: [215, 240], color: '#10B981', strokeDash: 'none' },
    { id: 'mumbai-bengaluru', from: [120, 195], to: [195, 310], color: '#38BDF8', strokeDash: '4,4' },
    { id: 'hyderabad-bengaluru', from: [215, 240], to: [195, 310], color: '#22D3EE', strokeDash: '4,4' },
    { id: 'hyderabad-kolkata', from: [215, 240], to: [320, 145], color: '#F43F5E', strokeDash: '3,3' },
  ];

  return (
    <div className="live-flow-card" aria-label="Live Shipment Flow Network Map">
      <div className="live-flow-header">
        <div className="live-flow-title-wrap">
          <h2 className="live-flow-title">Live Shipment Flow</h2>
          <span className="live-flow-pill">
            <span className="live-pulse-dot" /> Real-time
          </span>
        </div>

        {/* Legend */}
        <div className="live-flow-legend">
          <span className="legend-item"><span className="legend-dot in-transit" /> In Transit</span>
          <span className="legend-item"><span className="legend-triangle delayed" /> Delayed</span>
          <span className="legend-item"><span className="legend-dot delivered" /> Delivered</span>
          <span className="legend-item"><span className="legend-dot high-risk" /> High Risk</span>
        </div>
      </div>

      <div className="live-flow-viewport" style={{ transform: `scale(${zoomLevel})`, transformOrigin: 'center center', transition: 'transform 0.25s ease' }}>
        <svg
          viewBox="0 0 420 380"
          className="live-flow-svg"
          xmlns="http://www.w3.org/2000/svg"
        >
          <defs>
            {/* Soft grid background */}
            <radialGradient id="mapGlow" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#1E3A8A" stopOpacity="0.25" />
              <stop offset="100%" stopColor="#0B1220" stopOpacity="0" />
            </radialGradient>

            <filter id="glowFilter" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="3" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>

          {/* Regional Map Outline Silhouette */}
          <path
            d="M 160 30 C 230 20 270 45 280 80 C 330 95 380 120 360 170 C 340 210 290 230 270 270 C 240 330 200 360 180 365 C 160 330 140 280 120 240 C 90 200 70 160 100 120 C 130 90 140 50 160 30 Z"
            fill="#0E1A30"
            stroke="rgba(59, 130, 246, 0.2)"
            strokeWidth="1.5"
          />

          {/* Background Ambient Network Glow */}
          <circle cx="210" cy="190" r="160" fill="url(#mapGlow)" />

          {/* Transit Route Corridors with Animated Dash */}
          {routes.map((route) => (
            <g key={route.id}>
              <line
                x1={route.from[0]}
                y1={route.from[1]}
                x2={route.to[0]}
                y2={route.to[1]}
                stroke={route.color}
                strokeWidth="2"
                strokeDasharray={route.strokeDash}
                strokeOpacity="0.85"
                filter="url(#glowFilter)"
              />
              {/* Traveling Pulse Particle */}
              <circle
                r="3"
                fill="#FFFFFF"
                className="animated-pulse-vehicle"
              >
                <animateMotion
                  path={`M ${route.from[0]} ${route.from[1]} L ${route.to[0]} ${route.to[1]}`}
                  dur="4s"
                  repeatCount="indefinite"
                />
              </circle>
            </g>
          ))}

          {/* Hub Nodes */}
          {hubs.map((hub) => (
            <g
              key={hub.id}
              className="map-hub-group"
              onClick={() => setActiveCity(hub)}
              style={{ cursor: 'pointer' }}
            >
              {/* Pulsing ring */}
              <circle
                cx={hub.x}
                cy={hub.y}
                r="10"
                fill={hub.color}
                fillOpacity="0.2"
                className="pulse-halo"
              />
              {/* Node core */}
              <circle
                cx={hub.x}
                cy={hub.y}
                r="5"
                fill={hub.color}
                stroke="#FFFFFF"
                strokeWidth="1.5"
              />
              {/* Label */}
              <text
                x={hub.x + (hub.id === 'mumbai' ? -12 : 10)}
                y={hub.y + 4}
                fill="#F8FAFC"
                fontSize="11"
                fontWeight="600"
                textAnchor={hub.id === 'mumbai' ? 'end' : 'start'}
                className="map-city-label"
              >
                {hub.name}
              </text>
            </g>
          ))}
        </svg>

        {/* Floating Active Shipments Overlay matching Reference */}
        <div
          className="map-floating-kpi"
          onClick={() => onNavigate && onNavigate('shipments')}
          role="button"
          tabIndex={0}
          title="Inspect fleet shipments"
        >
          <div className="floating-kpi-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="1" y="3" width="15" height="13" />
              <polygon points="16 8 20 8 23 11 23 16 16 16 16 8" />
              <circle cx="5.5" cy="18.5" r="2.5" />
              <circle cx="18.5" cy="18.5" r="2.5" />
            </svg>
          </div>
          <div className="floating-kpi-details">
            <span className="floating-kpi-title">Active Shipments</span>
            <span className="floating-kpi-val">1,248</span>
            <span className="floating-kpi-sub">Across 5 warehouses ›</span>
          </div>
        </div>

        {/* Interactive Zoom Controls */}
        <div className="map-zoom-controls">
          <button
            type="button"
            className="btn-map-control"
            onClick={() => setZoomLevel((z) => Math.min(z + 0.15, 1.45))}
            title="Zoom In"
            aria-label="Zoom In"
          >
            +
          </button>
          <button
            type="button"
            className="btn-map-control"
            onClick={() => setZoomLevel((z) => Math.max(z - 0.15, 0.85))}
            title="Zoom Out"
            aria-label="Zoom Out"
          >
            −
          </button>
          <button
            type="button"
            className="btn-map-control"
            onClick={() => setZoomLevel(1)}
            title="Reset Map Orientation"
            aria-label="Reset View"
          >
            ⌖
          </button>
        </div>

        {/* City Tooltip Popup */}
        {activeCity && (
          <div className="city-popup" style={{ position: 'absolute', top: 12, left: 14 }}>
            <strong>{activeCity.name} Logistics Node</strong>
            <span>Active Manifests: {activeCity.activeLoads}</span>
            <span>Status: {activeCity.status.replace('_', ' ')}</span>
            <button className="city-popup-close" onClick={() => setActiveCity(null)}>×</button>
          </div>
        )}
      </div>
    </div>
  );
}
