import React from 'react';

/**
 * FeatureShortcutCards
 * 4 cards matching the reference design bottom row:
 * 1. Shipment Rescue Center
 * 2. What-If Disruption Simulator
 * 3. Operational Recommendations
 * 4. Analytics & Insights
 */
export default function FeatureShortcutCards({ onNavigate }) {
  const cards = [
    {
      id: 'rescue',
      title: 'Shipment Rescue Center',
      description: 'Find and fix operational bottlenecks using real-time data and rule-based alerts.',
      btnLabel: 'Open Center →',
      route: 'rescue',
      iconColor: '#F59E0B',
      iconSvg: (
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
        </svg>
      ),
      illustration: (
        <svg width="64" height="42" viewBox="0 0 64 42" fill="none" className="shortcut-illu">
          <rect x="6" y="14" width="22" height="22" rx="3" fill="#1E293B" stroke="#3B82F6" strokeWidth="1.5" />
          <path d="M6 22 H28 M17 14 V36" stroke="#3B82F6" strokeWidth="1" strokeDasharray="2,2" />
          <rect x="34" y="8" width="24" height="28" rx="3" fill="#1E293B" stroke="#F59E0B" strokeWidth="1.5" />
          <circle cx="46" cy="22" r="5" fill="#F59E0B" fillOpacity="0.3" stroke="#F59E0B" strokeWidth="1" />
        </svg>
      ),
    },
    {
      id: 'simulator',
      title: 'What-If Disruption Simulator',
      description: 'Model disruptions and test recovery strategies — no database changes.',
      btnLabel: 'Run Simulation →',
      route: 'simulator',
      iconColor: '#22D3EE',
      iconSvg: (
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="18" cy="5" r="3" />
          <circle cx="6" cy="12" r="3" />
          <circle cx="18" cy="19" r="3" />
          <line x1="8.59" y1="13.51" x2="15.42" y2="17.49" />
          <line x1="15.41" y1="6.51" x2="8.59" y2="10.49" />
        </svg>
      ),
      illustration: (
        <svg width="64" height="42" viewBox="0 0 64 42" fill="none" className="shortcut-illu">
          <circle cx="18" cy="21" r="5" fill="#22D3EE" fillOpacity="0.4" stroke="#22D3EE" strokeWidth="1.5" />
          <circle cx="46" cy="12" r="4" fill="#3B82F6" fillOpacity="0.4" stroke="#3B82F6" strokeWidth="1.5" />
          <circle cx="48" cy="30" r="4" fill="#38BDF8" fillOpacity="0.4" stroke="#38BDF8" strokeWidth="1.5" />
          <line x1="23" y1="19" x2="42" y2="14" stroke="#22D3EE" strokeWidth="1.5" strokeDasharray="3,3" />
          <line x1="23" y1="23" x2="44" y2="28" stroke="#38BDF8" strokeWidth="1.5" />
        </svg>
      ),
    },
    {
      id: 'recommendations',
      title: 'Operational Recommendations',
      description: 'Get explainable, human-reviewed suggestions for better outcomes.',
      btnLabel: 'View Recommendations →',
      route: 'recommendations',
      iconColor: '#FBBF24',
      iconSvg: (
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M9 18h6 M10 22h4 M15 2a6 6 0 0 0-6 6c0 2 1 3.5 2 4.5V14h4v-1.5c1-1 2-2.5 2-4.5a6 6 0 0 0-6-6z" />
        </svg>
      ),
      illustration: (
        <svg width="64" height="42" viewBox="0 0 64 42" fill="none" className="shortcut-illu">
          <rect x="14" y="6" width="36" height="32" rx="4" fill="#1E293B" stroke="#38BDF8" strokeWidth="1.5" />
          <path d="M22 14 H42 M22 20 H36 M22 26 H32" stroke="#94A3B8" strokeWidth="1.5" strokeLinecap="round" />
          <circle cx="42" cy="26" r="6" fill="#10B981" />
          <path d="M39 26 L41 28 L45 24" stroke="#FFFFFF" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      ),
    },
    {
      id: 'analytics',
      title: 'Analytics & Insights',
      description: 'Track performance, risks and trends across your supply chain.',
      btnLabel: 'View Analytics →',
      route: 'analytics',
      iconColor: '#38BDF8',
      iconSvg: (
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M18 20V10 M12 20V4 M6 20V14" />
        </svg>
      ),
      illustration: (
        <svg width="64" height="42" viewBox="0 0 64 42" fill="none" className="shortcut-illu">
          <rect x="10" y="24" width="7" height="14" rx="1.5" fill="#3B82F6" />
          <rect x="22" y="16" width="7" height="22" rx="1.5" fill="#38BDF8" />
          <rect x="34" y="8" width="7" height="30" rx="1.5" fill="#22D3EE" />
          <rect x="46" y="18" width="7" height="20" rx="1.5" fill="#60A5FA" />
        </svg>
      ),
    },
  ];

  return (
    <div className="feature-shortcuts-grid" aria-label="Core Operational Capabilities">
      {cards.map((card) => (
        <div key={card.id} className="shortcut-card">
          <div className="shortcut-top">
            <div className="shortcut-icon-circle" style={{ color: card.iconColor }}>
              {card.iconSvg}
            </div>
            <h3 className="shortcut-title">{card.title}</h3>
          </div>

          <p className="shortcut-desc">{card.description}</p>

          <div className="shortcut-bottom">
            <button
              type="button"
              className="btn-shortcut-action"
              onClick={() => onNavigate && onNavigate(card.route)}
            >
              {card.btnLabel}
            </button>
            <div className="shortcut-illustration-box" aria-hidden="true">
              {card.illustration}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
