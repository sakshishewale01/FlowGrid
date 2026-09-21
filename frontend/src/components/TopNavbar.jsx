import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import RoleBadge from './RoleBadge';

export default function TopNavbar({ 
  onToggleSidebar, 
  backendHealth, 
  isCheckingHealth, 
  onCheckHealth,
  pageTitle = "Logistics Overview"
}) {
  const { user, logout } = useAuth();
  const [isProfileMenuOpen, setIsProfileMenuOpen] = useState(false);
  const profileMenuRef = useRef(null);

  const currentDate = new Date().toLocaleDateString('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  });

  // Calculate user initials
  const getUserInitials = (name) => {
    if (!name) return 'FG';
    const parts = name.trim().split(/\s+/);
    if (parts.length === 1) return parts[0].substring(0, 2).toUpperCase();
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  };

  const initials = getUserInitials(user?.name);

  // Close profile dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (profileMenuRef.current && !profileMenuRef.current.contains(event.target)) {
        setIsProfileMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

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

        {/* User Profile Badge with Interactive Dropdown */}
        <div className="profile-menu-container" ref={profileMenuRef}>
          <button
            className="user-profile-badge interactive"
            id="user-profile-badge"
            onClick={() => setIsProfileMenuOpen(!isProfileMenuOpen)}
            aria-expanded={isProfileMenuOpen}
            aria-haspopup="true"
            title="Open user profile menu"
          >
            <div className="user-avatar">{initials}</div>
            <div className="user-info-text">
              <div className="user-name">{user?.name || 'Sarah Jenkins'}</div>
              <div className="user-role-line">
                <RoleBadge role={user?.role} size="small" />
              </div>
            </div>
            <svg
              className={`user-chevron ${isProfileMenuOpen ? 'open' : ''}`}
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <polyline points="6 9 12 15 18 9" />
            </svg>
          </button>

          {/* Dropdown Menu */}
          {isProfileMenuOpen && (
            <div className="profile-dropdown-menu" id="user-profile-dropdown" role="menu">
              <div className="profile-dropdown-header">
                <div className="dropdown-user-avatar">{initials}</div>
                <div className="dropdown-user-details">
                  <span className="dropdown-user-name">{user?.name || 'Authorized User'}</span>
                  <span className="dropdown-user-email">{user?.email || 'user@flowgrid.io'}</span>
                  <div className="dropdown-role-tag">
                    <RoleBadge role={user?.role} size="normal" />
                  </div>
                </div>
              </div>

              <div className="profile-dropdown-divider" />

              <div className="profile-dropdown-section">
                <div className="dropdown-info-item">
                  <span className="info-key">Session:</span>
                  <span className="info-val">Active JWT</span>
                </div>
                <div className="dropdown-info-item">
                  <span className="info-key">User ID:</span>
                  <span className="info-val">#{user?.id ?? '1'}</span>
                </div>
                <div className="dropdown-info-item">
                  <span className="info-key">Account Status:</span>
                  <span className="info-val text-success">Verified Active</span>
                </div>
              </div>

              <div className="profile-dropdown-divider" />

              <button
                className="profile-dropdown-logout-btn"
                id="btn-navbar-logout"
                onClick={() => {
                  setIsProfileMenuOpen(false);
                  logout();
                }}
                role="menuitem"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                  <polyline points="16 17 21 12 16 7" />
                  <line x1="21" y1="12" x2="9" y2="12" />
                </svg>
                <span>Sign Out</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
