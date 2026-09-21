import React from 'react';
import { useAuth } from '../context/AuthContext';
import RoleBadge from './RoleBadge';

const NAV_ITEMS = [
  { id: 'dashboard', label: 'Dashboard', icon: 'M3 3h7v7H3V3zm11 0h7v7h-7V3zm-11 11h7v7H3v-7zm11 0h7v7h-7v-7z' },
  { id: 'shipments', label: 'Shipments', icon: 'M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4' },
  { id: 'warehouses', label: 'Warehouses', icon: 'M3 21h18M3 7v14m18-14v14M6 11h4m-4 4h4m4-4h4m-4 4h4M9 3h6l3 4H6l3-4z' },
  { id: 'inventory', label: 'Inventory', icon: 'M4 6h16M4 10h16M4 14h16M4 18h16' },
  { id: 'drivers', label: 'Drivers', icon: 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z' },
  { id: 'routes', label: 'Routes', icon: 'M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7' },
  { id: 'analytics', label: 'Analytics', icon: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z' },
  { id: 'settings', label: 'Settings', icon: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z' },
];

export default function Sidebar({ activeTab, setActiveTab, isOpen, setIsOpen }) {
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
        {/* Brand Header */}
        <div className="sidebar-brand">
          <div className="brand-badge">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect>
              <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path>
            </svg>
          </div>
          <div className="brand-text-block">
            <span className="brand-name">FLOWGRID</span>
            <span className="brand-tag">OPS CONTROL</span>
          </div>
        </div>

        {/* Navigation links */}
        <nav className="sidebar-nav" aria-label="Main Navigation">
          <div className="nav-group-label">OPERATIONS</div>
          {NAV_ITEMS.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                id={`nav-${item.id}`}
                className={`sidebar-link ${isActive ? 'active' : ''}`}
                onClick={() => {
                  setActiveTab(item.id);
                  if (window.innerWidth < 1024) {
                    setIsOpen(false);
                  }
                }}
              >
                <svg className="nav-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                  <path d={item.icon} />
                </svg>
                <span className="nav-label">{item.label}</span>
                {item.id === 'shipments' && <span className="nav-pill">384</span>}
                {item.id === 'drivers' && <span className="nav-pill neutral">42</span>}
              </button>
            );
          })}
        </nav>

        {/* Authenticated User & System Node Footer */}
        <div className="sidebar-footer">
          {/* User Session Mini Card */}
          {user && (
            <div className="sidebar-user-card" id="sidebar-user-card">
              <div className="sidebar-user-info">
                <div className="sidebar-user-name">{user.name}</div>
                <div className="sidebar-user-meta">
                  <RoleBadge role={user.role} size="small" />
                  <span className="sidebar-user-id">#{user.id}</span>
                </div>
              </div>
              <button
                className="sidebar-logout-btn"
                id="btn-sidebar-logout"
                onClick={logout}
                title="Sign out of FlowGrid"
                aria-label="Sign out"
              >
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                  <polyline points="16 17 21 12 16 7" />
                  <line x1="21" y1="12" x2="9" y2="12" />
                </svg>
              </button>
            </div>
          )}

          <div className="system-node-card">
            <div className="node-header">
              <span className="pulse-indicator"></span>
              <span className="node-title">CONTROL NODE: CHI-01</span>
            </div>
            <div className="node-meta">FastAPI Core • React v19</div>
            <div className="node-version">Version 1.0.0 (Phase 14)</div>
          </div>
        </div>
      </aside>
    </>
  );
}
