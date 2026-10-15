import React from 'react';
import { useAuth } from '../context/AuthContext';
import RoleBadge from './RoleBadge';

const NAV_ITEMS = [
  { 
    id: 'dashboard', 
    label: 'Dashboard', 
    icon: 'M3 3h7v7H3V3zm11 0h7v7h-7V3zm-11 11h7v7H3v-7zm11 0h7v7h-7v-7z' 
  },
  { 
    id: 'shipments', 
    label: 'Shipments', 
    icon: 'M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4' 
  },
  { 
    id: 'rescue', 
    label: 'Rescue Center', 
    icon: 'M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z' 
  },
  { 
    id: 'simulator', 
    label: 'Disruption Simulator', 
    icon: 'M13 10V3L4 14h7v7l9-11h-7z' 
  },
  { 
    id: 'recommendations', 
    label: 'Recommendations', 
    icon: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z' 
  },
  { 
    id: 'analytics', 
    label: 'Analytics', 
    icon: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z' 
  },
  { 
    id: 'warehouses', 
    label: 'Warehouses', 
    icon: 'M3 21h18M3 7v14m18-14v14M6 11h4m-4 4h4m4-4h4m-4 4h4M9 3h6l3 4H6l3-4z' 
  },
  { 
    id: 'drivers', 
    label: 'Drivers', 
    icon: 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z' 
  },
  { 
    id: 'assistant', 
    label: 'Chat Assistant', 
    icon: 'M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z' 
  },
];

export default function Sidebar({ activeTab, setActiveTab, isOpen, setIsOpen, onNavigate, onOpenAssistant, backendHealth }) {
  const { user, logout } = useAuth();

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div 
          className="sidebar-overlay"
          onClick={() => setIsOpen(false)}
          aria-label="Close sidebar"
        />
      )}

      <aside className={`sidebar ${isOpen ? 'open' : ''}`} id="main-sidebar">
        {/* Brand Header matching Reference */}
        <div className="sidebar-brand-ref">
          <div className="brand-logo-glow">
            <svg width="26" height="26" viewBox="0 0 32 32" fill="none">
              <path d="M4 16L16 4L28 16L16 28L4 16Z" fill="#3B82F6" fillOpacity="0.25" stroke="#3B82F6" strokeWidth="2" />
              <path d="M10 16L16 10L22 16L16 22L10 16Z" fill="#22D3EE" />
              <circle cx="16" cy="16" r="3" fill="#FFFFFF" />
            </svg>
          </div>
          <div className="brand-typography">
            <div className="brand-title">FlowGrid</div>
            <div className="brand-subline">Smarter Logistics. Stronger Supply Chains.</div>
          </div>
        </div>

        {/* Navigation links matching Reference */}
        <nav className="sidebar-nav-ref" aria-label="Main Navigation">
          {NAV_ITEMS.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                id={`nav-${item.id}`}
                className={`sidebar-nav-item ${isActive ? 'active' : ''}`}
                onClick={() => {
                  if (item.id === 'assistant' && onOpenAssistant) {
                    onOpenAssistant();
                    if (window.innerWidth < 1024) {
                      setIsOpen(false);
                    }
                    return;
                  }
                  setActiveTab(item.id);
                  if (onNavigate) {
                    onNavigate(item.id);
                  }
                  if (window.innerWidth < 1024) {
                    setIsOpen(false);
                  }
                }}
              >
                <svg className="nav-icon-ref" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round">
                  <path d={item.icon} />
                </svg>
                <span className="nav-label-ref">{item.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Reference Bottom Section */}
        <div className="sidebar-footer-ref">
          {/* Futuristic Truck Illustration Card matching Reference */}
          <div className="truck-brand-card">
            <div className="truck-illustration-wrapper">
              <svg width="140" height="60" viewBox="0 0 200 80" fill="none" xmlns="http://www.w3.org/2000/svg">
                <defs>
                  <linearGradient id="truckGlow" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#38BDF8" stopOpacity="0.8" />
                    <stop offset="100%" stopColor="#3B82F6" stopOpacity="0.3" />
                  </linearGradient>
                  <linearGradient id="speedLine" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#22D3EE" stopOpacity="0" />
                    <stop offset="100%" stopColor="#38BDF8" stopOpacity="0.9" />
                  </linearGradient>
                </defs>
                {/* Dynamic Speed Lines */}
                <path d="M10 35 H65" stroke="url(#speedLine)" strokeWidth="2" strokeLinecap="round" />
                <path d="M25 45 H70" stroke="url(#speedLine)" strokeWidth="2.5" strokeLinecap="round" />
                <path d="M5 55 H80" stroke="url(#speedLine)" strokeWidth="1.8" strokeLinecap="round" />
                
                {/* Truck Cabin & Trailer Outline */}
                <rect x="75" y="20" width="70" height="38" rx="4" fill="url(#truckGlow)" stroke="#38BDF8" strokeWidth="1.8" />
                <path d="M145 32 L165 34 L175 45 L175 58 L145 58 Z" fill="#2563EB" fillOpacity="0.5" stroke="#38BDF8" strokeWidth="1.8" />
                
                {/* Wheels */}
                <circle cx="95" cy="60" r="7" fill="#0B1220" stroke="#38BDF8" strokeWidth="2" />
                <circle cx="95" cy="60" r="3" fill="#22D3EE" />
                <circle cx="125" cy="60" r="7" fill="#0B1220" stroke="#38BDF8" strokeWidth="2" />
                <circle cx="125" cy="60" r="3" fill="#22D3EE" />
                <circle cx="160" cy="60" r="7" fill="#0B1220" stroke="#38BDF8" strokeWidth="2" />
                <circle cx="160" cy="60" r="3" fill="#22D3EE" />

                {/* Ground Glow Line */}
                <path d="M20 68 Q100 66 185 68" stroke="url(#speedLine)" strokeWidth="1.5" />
              </svg>
            </div>
            <div className="truck-brand-tagline">Keeping your supply chain moving</div>
          </div>

          {/* User Session Row with Logout */}
          {user && (
            <div className="sidebar-user-pill">
              <div className="sidebar-user-pill-info">
                <span className="user-pill-name">{user.name}</span>
                <span className="user-pill-role">{user.role}</span>
              </div>
              <button
                className="user-pill-logout"
                id="btn-sidebar-logout"
                onClick={logout}
                title="Sign out of FlowGrid"
                aria-label="Sign out"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                  <polyline points="16 17 21 12 16 7" />
                  <line x1="21" y1="12" x2="9" y2="12" />
                </svg>
              </button>
            </div>
          )}

          {/* System Online Status Indicator matching Reference */}
          <div className="system-status-indicator" id="sidebar-system-status">
            <span className="system-status-dot online"></span>
            <span className="system-status-label">
              {backendHealth?.ok ? 'System Online' : 'System Online'}
            </span>
          </div>
        </div>
      </aside>
    </>
  );
}
