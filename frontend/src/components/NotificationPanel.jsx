/**
 * FlowGrid In-App Notification Panel
 * ===================================
 * Interactive drop-down notification center displaying live shipment transitions,
 * low-stock inventory warnings, and system alerts.
 */

import React, { useState, useRef, useEffect } from 'react';
import { useNotifications } from '../context/NotificationContext';

export default function NotificationPanel({ isOpen, onClose, onSelectShipment }) {
  const {
    notifications,
    unreadCount,
    markAsRead,
    markAllAsRead,
    clearNotification,
    clearAll,
  } = useNotifications();

  const [activeFilter, setActiveFilter] = useState('all'); // 'all' | 'unread'
  const panelRef = useRef(null);

  // Close panel on outside click
  useEffect(() => {
    if (!isOpen) return;
    const handleClickOutside = (e) => {
      if (
        panelRef.current &&
        !panelRef.current.contains(e.target) &&
        !e.target.closest('#btn-nav-notifications')
      ) {
        onClose();
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const filteredNotifications = notifications.filter((n) => {
    if (activeFilter === 'unread') return !n.read;
    return true;
  });

  const formatTimeAgo = (isoString) => {
    if (!isoString) return 'Just now';
    try {
      const now = new Date();
      const past = new Date(isoString);
      const diffSec = Math.floor((now - past) / 1000);
      if (diffSec < 60) return 'Just now';
      if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`;
      if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}h ago`;
      return past.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    } catch {
      return 'Recent';
    }
  };

  const getSeverityIcon = (type, severity) => {
    if (type === 'LOW_STOCK') {
      return (
        <div
          style={{
            width: '28px',
            height: '28px',
            borderRadius: '50%',
            background: 'rgba(234, 179, 8, 0.18)',
            color: '#FACC15',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
          }}
        >
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
            <line x1="12" y1="9" x2="12" y2="13" />
            <line x1="12" y1="17" x2="12.01" y2="17" />
          </svg>
        </div>
      );
    }

    if (severity === 'success') {
      return (
        <div
          style={{
            width: '28px',
            height: '28px',
            borderRadius: '50%',
            background: 'rgba(16, 185, 129, 0.18)',
            color: '#10B981',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
          }}
        >
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <polyline points="20 6 9 17 4 12" />
          </svg>
        </div>
      );
    }

    if (severity === 'error') {
      return (
        <div
          style={{
            width: '28px',
            height: '28px',
            borderRadius: '50%',
            background: 'rgba(239, 68, 68, 0.18)',
            color: '#EF4444',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
          }}
        >
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </div>
      );
    }

    // Default info / shipment transit
    return (
      <div
        style={{
          width: '28px',
          height: '28px',
          borderRadius: '50%',
          background: 'rgba(56, 189, 248, 0.18)',
          color: '#38BDF8',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
        }}
      >
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <rect x="1" y="3" width="15" height="13" />
          <polygon points="16 8 20 8 23 11 23 16 16 16 16 8" />
          <circle cx="5.5" cy="18.5" r="2.5" />
          <circle cx="18.5" cy="18.5" r="2.5" />
        </svg>
      </div>
    );
  };

  return (
    <div
      ref={panelRef}
      className="notification-dropdown-panel"
      role="region"
      aria-label="Dispatch and stock notifications"
      style={{
        position: 'absolute',
        top: 'calc(100% + 8px)',
        right: '0',
        width: '380px',
        maxWidth: '92vw',
        background: '#0F172A',
        border: '1px solid rgba(51, 65, 85, 0.85)',
        borderRadius: '12px',
        boxShadow: '0 20px 35px -5px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(255, 255, 255, 0.05)',
        zIndex: 1050,
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        animation: 'fadeIn 0.15s ease-out',
      }}
    >
      {/* Panel Header */}
      <div
        style={{
          padding: '14px 16px',
          borderBottom: '1px solid rgba(51, 65, 85, 0.6)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: 'rgba(15, 23, 42, 0.95)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontWeight: 700, fontSize: '0.92rem', color: '#F1F5F9' }}>
            Notifications
          </span>
          {unreadCount > 0 && (
            <span
              style={{
                background: '#0284C7',
                color: '#FFF',
                fontSize: '0.70rem',
                fontWeight: 700,
                padding: '2px 7px',
                borderRadius: '10px',
              }}
            >
              {unreadCount} new
            </span>
          )}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {unreadCount > 0 && (
            <button
              type="button"
              onClick={markAllAsRead}
              style={{
                background: 'none',
                border: 'none',
                color: '#38BDF8',
                fontSize: '0.75rem',
                cursor: 'pointer',
                fontWeight: 600,
                padding: '2px 4px',
              }}
              title="Mark all notifications as read"
            >
              Mark all read
            </button>
          )}
          {notifications.length > 0 && (
            <button
              type="button"
              onClick={clearAll}
              style={{
                background: 'none',
                border: 'none',
                color: '#94A3B8',
                fontSize: '0.75rem',
                cursor: 'pointer',
                padding: '2px 4px',
              }}
              title="Clear all alerts"
            >
              Clear
            </button>
          )}
        </div>
      </div>

      {/* Filter Tabs */}
      <div
        style={{
          display: 'flex',
          gap: '8px',
          padding: '8px 16px',
          borderBottom: '1px solid rgba(51, 65, 85, 0.4)',
          background: 'rgba(30, 41, 59, 0.4)',
        }}
      >
        <button
          type="button"
          onClick={() => setActiveFilter('all')}
          style={{
            background: activeFilter === 'all' ? 'rgba(56, 189, 248, 0.15)' : 'transparent',
            color: activeFilter === 'all' ? '#38BDF8' : '#94A3B8',
            border: activeFilter === 'all' ? '1px solid rgba(56, 189, 248, 0.3)' : '1px solid transparent',
            padding: '4px 10px',
            borderRadius: '6px',
            fontSize: '0.74rem',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          All ({notifications.length})
        </button>
        <button
          type="button"
          onClick={() => setActiveFilter('unread')}
          style={{
            background: activeFilter === 'unread' ? 'rgba(56, 189, 248, 0.15)' : 'transparent',
            color: activeFilter === 'unread' ? '#38BDF8' : '#94A3B8',
            border: activeFilter === 'unread' ? '1px solid rgba(56, 189, 248, 0.3)' : '1px solid transparent',
            padding: '4px 10px',
            borderRadius: '6px',
            fontSize: '0.74rem',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          Unread ({unreadCount})
        </button>
      </div>

      {/* Notifications List */}
      <div
        style={{
          maxHeight: '360px',
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {filteredNotifications.length === 0 ? (
          <div
            style={{
              padding: '36px 20px',
              textAlign: 'center',
              color: '#64748B',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
              <path d="M13.73 21a2 2 0 0 1-3.46 0" />
            </svg>
            <span style={{ fontSize: '0.82rem', fontWeight: 500 }}>
              {activeFilter === 'unread' ? 'No unread notifications' : 'No notifications yet'}
            </span>
            <span style={{ fontSize: '0.74rem' }}>
              Live dispatch updates and stock alerts will appear here.
            </span>
          </div>
        ) : (
          filteredNotifications.map((n) => (
            <div
              key={n.id}
              onClick={() => {
                if (!n.read) markAsRead(n.id);
                if (n.type === 'SHIPMENT' && n.metadata?.shipmentId && onSelectShipment) {
                  onSelectShipment(n.metadata.shipmentId);
                  onClose();
                }
              }}
              style={{
                display: 'flex',
                gap: '12px',
                padding: '12px 16px',
                borderBottom: '1px solid rgba(51, 65, 85, 0.35)',
                background: n.read ? 'transparent' : 'rgba(15, 23, 42, 0.5)',
                cursor: 'pointer',
                transition: 'background 0.15s ease',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = 'rgba(30, 41, 59, 0.5)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = n.read ? 'transparent' : 'rgba(15, 23, 42, 0.5)';
              }}
            >
              {getSeverityIcon(n.type, n.severity)}

              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: '6px' }}>
                  <span
                    style={{
                      fontSize: '0.80rem',
                      fontWeight: n.read ? 600 : 700,
                      color: n.read ? '#CBD5E1' : '#F1F5F9',
                    }}
                  >
                    {n.title}
                  </span>
                  <span style={{ fontSize: '0.68rem', color: '#64748B', whiteSpace: 'nowrap' }}>
                    {formatTimeAgo(n.timestamp)}
                  </span>
                </div>

                <p
                  style={{
                    fontSize: '0.74rem',
                    color: n.read ? '#94A3B8' : '#CBD5E1',
                    margin: '3px 0 6px 0',
                    lineHeight: 1.4,
                  }}
                >
                  {n.message}
                </p>

                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
                  {!n.read && (
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        markAsRead(n.id);
                      }}
                      style={{
                        background: 'none',
                        border: 'none',
                        color: '#38BDF8',
                        fontSize: '0.70rem',
                        cursor: 'pointer',
                        padding: 0,
                      }}
                    >
                      Mark read
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      clearNotification(n.id);
                    }}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: '#64748B',
                      fontSize: '0.70rem',
                      cursor: 'pointer',
                      padding: 0,
                    }}
                  >
                    Dismiss
                  </button>
                </div>
              </div>

              {!n.read && (
                <div
                  style={{
                    width: '7px',
                    height: '7px',
                    borderRadius: '50%',
                    background: '#38BDF8',
                    alignSelf: 'center',
                    flexShrink: 0,
                  }}
                />
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
