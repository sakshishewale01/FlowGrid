import React from 'react';

export default function TopNavbar({ 
  onToggleSidebar, 
  backendHealth, 
  isCheckingHealth, 
  onCheckHealth,
  pageTitle = "Logistics Overview"
}) {
  const currentDate = new Date().toLocaleDateString('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  });

  return (
    <header className="top-navbar" id="top-navbar">
      <div className="navbar-left">
        {/* Mobile Hamburger Toggle */}
        <button
          className="mobile-toggle-btn"
          id="mobile-sidebar-toggle"
          onClick={onToggleSidebar}
          aria-label="Toggle navigation menu"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="3" y1="12" x2="21" y2="12"></line>
            <line x1="3" y1="6" x2="21" y2="6"></line>
            <line x1="3" y1="18" x2="21" y2="18"></line>
          </svg>
        </button>

        {/* Page Title in Topbar */}
        <div className="navbar-page-title">
          <span className="page-breadcrumb">FLOWGRID /</span>
          <span className="page-current">{pageTitle}</span>
        </div>

        {/* Global Search */}
        <div className="search-bar-wrapper">
          <svg className="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
          </svg>
          <input
            type="text"
            className="search-input"
            id="global-search-input"
            placeholder="Search tracking #, SKU, warehouse, driver..."
          />
          <span className="search-shortcut">⌘K</span>
        </div>
      </div>

      <div className="navbar-right">
        {/* Operational Date */}
        <div className="date-badge" id="current-ops-date">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
            <line x1="16" y1="2" x2="16" y2="6"></line>
            <line x1="8" y1="2" x2="8" y2="6"></line>
            <line x1="3" y1="10" x2="21" y2="10"></line>
          </svg>
          <span>{currentDate}</span>
        </div>

        {/* Live Backend Connection Monitor */}
        <div className="backend-monitor-pill" id="backend-status-container">
          <span className={`status-led ${backendHealth?.ok ? 'connected' : backendHealth === null ? 'idle' : 'disconnected'}`}></span>
          <span className="backend-label">
            {backendHealth?.ok ? 'FastAPI Online' : isCheckingHealth ? 'Pinging...' : 'API Status'}
          </span>
          <button
            id="btn-nav-ping"
            className="btn-ping"
            onClick={onCheckHealth}
            disabled={isCheckingHealth}
            title="Ping /health on FastAPI server"
          >
            {isCheckingHealth ? '...' : 'Ping /health'}
          </button>
        </div>

        {/* Notifications Icon with Badge */}
        <div className="nav-icon-button" id="btn-nav-notifications" title="3 unread dispatch alerts">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
            <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
          </svg>
          <span className="notification-badge">3</span>
        </div>

        {/* User Profile Placeholder */}
        <div className="user-profile-badge" id="user-profile-badge">
          <div className="user-avatar">SJ</div>
          <div className="user-info-text">
            <div className="user-name">Sarah Jenkins</div>
            <div className="user-role-label">Operations Dispatcher</div>
          </div>
        </div>
      </div>
    </header>
  );
}
