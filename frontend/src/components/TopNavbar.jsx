import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNotifications } from '../context/NotificationContext';
import RoleBadge from './RoleBadge';
import NotificationPanel from './NotificationPanel';


export default function TopNavbar({ 
  onToggleSidebar, 
  backendHealth, 
  isCheckingHealth, 
  onCheckHealth,
  pageTitle = "Logistics Overview",
  onSearch = null,
  onOpenAssistant = null,
}) {
  const { user, logout } = useAuth();
  const { unreadCount } = useNotifications();
  const [searchQuery, setSearchQuery] = useState('');
  const [isProfileMenuOpen, setIsProfileMenuOpen] = useState(false);
  const [isNotificationOpen, setIsNotificationOpen] = useState(false);
  const [theme, setTheme] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('flowgrid_theme') || 'dark';
    }
    return 'dark';
  });
  const profileMenuRef = useRef(null);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('flowgrid_theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  };


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
            placeholder="Search shipments, warehouses, drivers..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && searchQuery.trim() && onSearch) {
                onSearch(searchQuery.trim());
              }
            }}
            aria-label="Search shipments, warehouses, drivers"
          />
          <button
            type="button"
            className="search-shortcut"
            onClick={() => searchQuery.trim() && onSearch && onSearch(searchQuery.trim())}
            style={{ cursor: 'pointer', background: 'none', border: 'none', color: 'inherit' }}
            title="Execute search"
          >
            ⏎
          </button>
        </div>
      </div>

      <div className="navbar-right">
        {/* Live Backend Connection Monitor */}
        <div 
          className="backend-monitor-pill" 
          id="backend-status-container"
          title={`FlowGrid Operational Telemetry • ${currentDate}`}
        >
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

        {/* Logistics Assistant Quick Launcher */}
        {onOpenAssistant && (
          <button
            type="button"
            className="nav-icon-button"
            id="btn-nav-assistant"
            onClick={onOpenAssistant}
            aria-label="Open FlowGrid Logistics Assistant"
            title="FlowGrid Logistics Assistant"
            style={{ cursor: 'pointer', background: 'none', border: 'none', color: '#38BDF8' }}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
            </svg>
          </button>
        )}

        {/* Notifications Icon with Badge & Dropdown Panel */}
        <div style={{ position: 'relative' }}>
          <button
            type="button"
            className="nav-icon-button"
            id="btn-nav-notifications"
            onClick={() => setIsNotificationOpen(!isNotificationOpen)}
            aria-expanded={isNotificationOpen}
            aria-label={`${unreadCount} notifications`}
            title={unreadCount > 0 ? `${unreadCount} unread alerts` : 'Notifications'}
            style={{ position: 'relative', cursor: 'pointer', background: 'none', border: 'none' }}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
              <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
            </svg>
            {unreadCount > 0 && (
              <span className="notification-badge" style={{ pointerEvents: 'none' }}>
                {unreadCount > 99 ? '99+' : unreadCount}
              </span>
            )}
          </button>

          <NotificationPanel
            isOpen={isNotificationOpen}
            onClose={() => setIsNotificationOpen(false)}
          />
        </div>

        {/* Theme Light/Dark Indicator Toggle */}
        <button
          type="button"
          className="nav-icon-button theme-toggle-btn"
          id="btn-nav-theme-toggle"
          onClick={toggleTheme}
          title={theme === 'dark' ? 'Switch to Light Theme' : 'Switch to Dark Theme'}
          aria-label={`Toggle Theme (Current: ${theme})`}
          style={{
            cursor: 'pointer',
            background: 'none',
            border: 'none',
            color: theme === 'dark' ? '#FBBF24' : '#38BDF8',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          {theme === 'dark' ? (
            /* Sun Icon when in Dark Mode (click to switch to light) */
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="5"></circle>
              <line x1="12" y1="1" x2="12" y2="3"></line>
              <line x1="12" y1="21" x2="12" y2="23"></line>
              <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
              <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
              <line x1="1" y1="12" x2="3" y2="12"></line>
              <line x1="21" y1="12" x2="23" y2="12"></line>
              <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
              <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
            </svg>
          ) : (
            /* Moon Icon when in Light Mode (click to switch to dark) */
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
            </svg>
          )}
        </button>


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
