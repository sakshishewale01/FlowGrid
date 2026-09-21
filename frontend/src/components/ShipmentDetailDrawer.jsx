import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { shipmentsApi } from '../api/shipments.js';
import { trackingApi } from '../api/tracking.js';
import { formatErrorMessage } from '../api/client.js';

const STATUS_TRANSITIONS = {
  CREATED: ['CONFIRMED', 'CANCELLED'],
  CONFIRMED: ['ASSIGNED', 'CANCELLED'],
  ASSIGNED: ['DISPATCHED', 'IN_TRANSIT', 'CANCELLED'],
  DISPATCHED: ['IN_TRANSIT', 'CANCELLED'],
  IN_TRANSIT: ['OUT_FOR_DELIVERY', 'DELIVERED', 'FAILED'],
  OUT_FOR_DELIVERY: ['DELIVERED', 'FAILED'],
  DELIVERED: [],
  FAILED: ['CONFIRMED', 'CANCELLED'],
  CANCELLED: [],
};

export default function ShipmentDetailDrawer({
  isOpen,
  onClose,
  shipment = null,
  onUpdated,
}) {
  const { user } = useAuth();
  const isAuthorized = user?.role === 'ADMIN' || user?.role === 'MANAGER';

  const [activeTab, setActiveTab] = useState('overview'); // 'overview' | 'tracking' | 'status'
  const [history, setHistory] = useState([]);
  const [events, setEvents] = useState([]);
  const [loadingTimeline, setLoadingTimeline] = useState(false);
  const [timelineError, setTimelineError] = useState(null);

  // Status transition state
  const [targetStatus, setTargetStatus] = useState('');
  const [statusRemarks, setStatusRemarks] = useState('');
  const [isUpdatingStatus, setIsUpdatingStatus] = useState(false);
  const [statusError, setStatusError] = useState(null);

  // Add event state
  const [eventLocation, setEventLocation] = useState('');
  const [eventNotes, setEventNotes] = useState('');
  const [isAddingEvent, setIsAddingEvent] = useState(false);
  const [eventError, setEventError] = useState(null);

  const loadTimelineData = useCallback(async (shipmentId) => {
    setLoadingTimeline(true);
    setTimelineError(null);
    try {
      const [histData, evData] = await Promise.allSettled([
        trackingApi.getStatusHistory(shipmentId),
        trackingApi.getTrackingEvents(shipmentId),
      ]);

      if (histData.status === 'fulfilled') {
        setHistory(histData.value || []);
      }
      if (evData.status === 'fulfilled') {
        setEvents(evData.value || []);
      }
    } catch (err) {
      setTimelineError(formatErrorMessage(err));
    } finally {
      setLoadingTimeline(false);
    }
  }, []);

  useEffect(() => {
    if (shipment && isOpen) {
      loadTimelineData(shipment.id);
      const possible = STATUS_TRANSITIONS[shipment.status] || [];
      setTargetStatus(possible[0] || '');
      setStatusRemarks('');
      setEventLocation('');
      setEventNotes('');
      setStatusError(null);
      setEventError(null);
    }
  }, [shipment, isOpen, loadTimelineData]);

  if (!isOpen || !shipment) return null;

  const allowedTransitions = STATUS_TRANSITIONS[shipment.status] || [];

  const handleStatusTransition = async (e) => {
    e.preventDefault();
    if (!targetStatus) return;
    setIsUpdatingStatus(true);
    setStatusError(null);
    try {
      const updated = await shipmentsApi.transitionStatus(shipment.id, {
        status: targetStatus,
        remarks: statusRemarks.trim() || undefined,
      });
      if (onUpdated) onUpdated(updated);
      loadTimelineData(shipment.id);
      setStatusRemarks('');
    } catch (err) {
      setStatusError(formatErrorMessage(err));
    } finally {
      setIsUpdatingStatus(false);
    }
  };

  const handleAddTrackingEvent = async (e) => {
    e.preventDefault();
    if (!eventLocation.trim()) {
      setEventError('Waypoint location is required.');
      return;
    }
    setIsAddingEvent(true);
    setEventError(null);
    try {
      await trackingApi.addTrackingEvent(shipment.id, {
        status: shipment.status,
        location: eventLocation.trim(),
        notes: eventNotes.trim() || undefined,
      });
      setEventLocation('');
      setEventNotes('');
      loadTimelineData(shipment.id);
    } catch (err) {
      setEventError(formatErrorMessage(err));
    } finally {
      setIsAddingEvent(false);
    }
  };

  return (
    <div className="modal-backdrop" onClick={onClose} role="dialog" aria-modal="true">
      <div className="modal-card modal-card-large drawer-card" onClick={(e) => e.stopPropagation()}>
        {/* Drawer Header */}
        <div className="modal-header">
          <div className="modal-header-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
            </svg>
          </div>
          <div className="modal-header-text">
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <h2 className="modal-title" style={{ fontFamily: 'monospace', letterSpacing: '0.04em' }}>
                {shipment.tracking_number}
              </h2>
              <span className={`status-badge ${shipment.status?.toLowerCase().replace(/_/g, '-')}`}>
                {shipment.status}
              </span>
            </div>
            <p className="modal-subtitle">
              Waybill Manifest #{shipment.id} • Registered {shipment.created_at ? new Date(shipment.created_at).toLocaleDateString() : 'Active'}
            </p>
          </div>
          <button type="button" className="modal-close-btn" onClick={onClose} aria-label="Close">×</button>
        </div>

        {/* Tab Navigation */}
        <div className="drawer-tab-bar" style={{
          display: 'flex',
          borderBottom: '1px solid rgba(51, 65, 85, 0.8)',
          padding: '0 24px',
          gap: '16px',
          marginBottom: '16px'
        }}>
          <button
            type="button"
            className={`tab-btn ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
            style={{
              background: 'none',
              border: 'none',
              borderBottom: activeTab === 'overview' ? '2px solid #38BDF8' : '2px solid transparent',
              color: activeTab === 'overview' ? '#38BDF8' : '#94A3B8',
              padding: '10px 4px',
              cursor: 'pointer',
              fontWeight: 600,
              fontSize: '0.85rem'
            }}
          >
            Waybill Overview
          </button>
          <button
            type="button"
            className={`tab-btn ${activeTab === 'tracking' ? 'active' : ''}`}
            onClick={() => setActiveTab('tracking')}
            style={{
              background: 'none',
              border: 'none',
              borderBottom: activeTab === 'tracking' ? '2px solid #38BDF8' : '2px solid transparent',
              color: activeTab === 'tracking' ? '#38BDF8' : '#94A3B8',
              padding: '10px 4px',
              cursor: 'pointer',
              fontWeight: 600,
              fontSize: '0.85rem'
            }}
          >
            Tracking Events ({events.length})
          </button>
          <button
            type="button"
            className={`tab-btn ${activeTab === 'history' ? 'active' : ''}`}
            onClick={() => setActiveTab('history')}
            style={{
              background: 'none',
              border: 'none',
              borderBottom: activeTab === 'history' ? '2px solid #38BDF8' : '2px solid transparent',
              color: activeTab === 'history' ? '#38BDF8' : '#94A3B8',
              padding: '10px 4px',
              cursor: 'pointer',
              fontWeight: 600,
              fontSize: '0.85rem'
            }}
          >
            Status Audit Log ({history.length})
          </button>
        </div>

        {/* Tab 1: Overview */}
        {activeTab === 'overview' && (
          <div className="drawer-content-body" style={{ padding: '0 24px 20px', maxHeight: '55vh', overflowY: 'auto' }}>
            <div className="manifest-grid-2">
              <div className="manifest-item">
                <span className="manifest-label">Origin Facility</span>
                <span className="manifest-value">{shipment.origin_warehouse?.name || `Warehouse #${shipment.origin_warehouse_id || 'N/A'}`}</span>
                <span className="manifest-sub">{shipment.origin_warehouse?.location || 'Central Depot'}</span>
              </div>

              <div className="manifest-item">
                <span className="manifest-label">Destination Address</span>
                <span className="manifest-value">{shipment.destination_address}</span>
                <span className="manifest-sub">{shipment.destination_city}, {shipment.destination_state} {shipment.destination_postal_code}</span>
              </div>

              <div className="manifest-item">
                <span className="manifest-label">Assigned Driver</span>
                <span className="manifest-value">
                  {shipment.assigned_driver
                    ? `Driver #${shipment.assigned_driver.id} (${shipment.assigned_driver.license_number})`
                    : 'Unassigned'}
                </span>
                <span className="manifest-sub">{shipment.assigned_driver?.phone_number || 'Mobile link pending'}</span>
              </div>

              <div className="manifest-item">
                <span className="manifest-label">Carrier Vehicle</span>
                <span className="manifest-value">
                  {shipment.assigned_vehicle
                    ? `${shipment.assigned_vehicle.registration_number} (${shipment.assigned_vehicle.vehicle_type})`
                    : 'Unassigned'}
                </span>
                <span className="manifest-sub">
                  {shipment.assigned_vehicle ? `Cap: ${shipment.assigned_vehicle.capacity} kg` : 'Payload pending'}
                </span>
              </div>

              <div className="manifest-item">
                <span className="manifest-label">Cargo Weight & Volume</span>
                <span className="manifest-value">{shipment.total_weight_kg ? `${shipment.total_weight_kg} kg` : '0 kg'}</span>
                <span className="manifest-sub">{shipment.total_volume_cbm ? `${shipment.total_volume_cbm} m³` : 'Standard freight'}</span>
              </div>

              <div className="manifest-item">
                <span className="manifest-label">Scheduled Dispatch</span>
                <span className="manifest-value">
                  {shipment.scheduled_pickup_at ? new Date(shipment.scheduled_pickup_at).toLocaleString() : 'Immediate Dispatch'}
                </span>
                <span className="manifest-sub">Priority Level: STANDARD</span>
              </div>
            </div>

            {/* Lifecycle Status Advancement Panel */}
            <div className="status-transition-box" style={{
              marginTop: '20px',
              padding: '16px',
              background: 'rgba(15, 23, 42, 0.6)',
              border: '1px solid rgba(51, 65, 85, 0.8)',
              borderRadius: '8px'
            }}>
              <h4 style={{ fontSize: '0.85rem', color: '#F1F5F9', marginBottom: '8px', fontWeight: 600 }}>
                Advance Shipment Lifecycle State
              </h4>

              {!isAuthorized ? (
                <p style={{ fontSize: '0.8rem', color: '#94A3B8' }}>
                  🔒 Status advancement requires ADMIN or MANAGER privileges. (Your role: {user?.role})
                </p>
              ) : allowedTransitions.length === 0 ? (
                <p style={{ fontSize: '0.8rem', color: '#10B981' }}>
                  ✓ This shipment has reached terminal lifecycle state ({shipment.status}). No further transitions allowed.
                </p>
              ) : (
                <form onSubmit={handleStatusTransition}>
                  {statusError && (
                    <div className="auth-alert error" style={{ marginBottom: '12px' }}>
                      <span className="auth-alert-text">{statusError}</span>
                    </div>
                  )}
                  <div className="form-row-2">
                    <div className="form-group" style={{ marginBottom: 0 }}>
                      <label className="form-label" style={{ fontSize: '0.78rem' }}>Next State *</label>
                      <select
                        className="form-input form-select"
                        value={targetStatus}
                        onChange={(e) => setTargetStatus(e.target.value)}
                        disabled={isUpdatingStatus}
                      >
                        {allowedTransitions.map((st) => (
                          <option key={st} value={st}>{st}</option>
                        ))}
                      </select>
                    </div>

                    <div className="form-group" style={{ marginBottom: 0 }}>
                      <label className="form-label" style={{ fontSize: '0.78rem' }}>Audit Remarks</label>
                      <input
                        type="text"
                        className="form-input"
                        placeholder="e.g. Scanned at outbound conveyor"
                        value={statusRemarks}
                        onChange={(e) => setStatusRemarks(e.target.value)}
                        disabled={isUpdatingStatus}
                      />
                    </div>
                  </div>

                  <button
                    type="submit"
                    className="btn-action primary"
                    style={{ marginTop: '12px' }}
                    disabled={isUpdatingStatus}
                  >
                    {isUpdatingStatus ? 'Transitioning...' : `Transition to ${targetStatus}`}
                  </button>
                </form>
              )}
            </div>
          </div>
        )}

        {/* Tab 2: Waypoint Tracking Events */}
        {activeTab === 'tracking' && (
          <div className="drawer-content-body" style={{ padding: '0 24px 20px', maxHeight: '55vh', overflowY: 'auto' }}>
            {/* Record Checkpoint Form (for ADMIN / MANAGER) */}
            {isAuthorized && (
              <div className="add-event-box" style={{
                marginBottom: '18px',
                padding: '14px',
                background: 'rgba(15, 23, 42, 0.6)',
                border: '1px solid rgba(51, 65, 85, 0.7)',
                borderRadius: '8px'
              }}>
                <h4 style={{ fontSize: '0.82rem', color: '#E2E8F0', marginBottom: '8px', fontWeight: 600 }}>
                  + Record Physical Waypoint Checkpoint
                </h4>
                {eventError && (
                  <div className="auth-alert error" style={{ marginBottom: '8px' }}>
                    <span className="auth-alert-text">{eventError}</span>
                  </div>
                )}
                <form onSubmit={handleAddTrackingEvent}>
                  <div className="form-row-2">
                    <div className="form-group" style={{ marginBottom: 0 }}>
                      <input
                        type="text"
                        className="form-input"
                        placeholder="Location (e.g. Weigh Station #4, Gary IN)"
                        value={eventLocation}
                        onChange={(e) => setEventLocation(e.target.value)}
                        disabled={isAddingEvent}
                      />
                    </div>
                    <div className="form-group" style={{ marginBottom: 0 }}>
                      <input
                        type="text"
                        className="form-input"
                        placeholder="Notes / Telematics breadcrumb"
                        value={eventNotes}
                        onChange={(e) => setEventNotes(e.target.value)}
                        disabled={isAddingEvent}
                      />
                    </div>
                  </div>
                  <button
                    type="submit"
                    className="btn-action primary"
                    style={{ marginTop: '10px', fontSize: '0.78rem', padding: '6px 14px' }}
                    disabled={isAddingEvent}
                  >
                    {isAddingEvent ? 'Recording...' : 'Log Waypoint'}
                  </button>
                </form>
              </div>
            )}

            {timelineError && (
              <div className="auth-alert error" style={{ marginBottom: '12px' }}>
                <span className="auth-alert-text">{timelineError}</span>
              </div>
            )}

            {/* Events Timeline */}
            {loadingTimeline ? (
              <div style={{ padding: '16px', color: '#94A3B8' }}>Loading waypoint history...</div>
            ) : events.length === 0 ? (
              <div style={{ padding: '24px', textAlign: 'center', color: '#64748B' }}>
                No waypoint checkpoints recorded for this shipment yet.
              </div>
            ) : (
              <div className="timeline-list">
                {events.map((ev, idx) => (
                  <div key={ev.id || idx} style={{
                    display: 'flex',
                    gap: '12px',
                    padding: '10px 0',
                    borderBottom: '1px solid rgba(51, 65, 85, 0.4)'
                  }}>
                    <div style={{
                      width: '10px',
                      height: '10px',
                      borderRadius: '50%',
                      background: '#38BDF8',
                      marginTop: '6px'
                    }} />
                    <div>
                      <div style={{ fontSize: '0.85rem', color: '#F1F5F9', fontWeight: 600 }}>
                        {ev.location}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: '#94A3B8' }}>
                        {ev.timestamp ? new Date(ev.timestamp).toLocaleString() : 'Checkpoint logged'}
                        {ev.notes && ` • "${ev.notes}"`}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Tab 3: Status Audit History */}
        {activeTab === 'history' && (
          <div className="drawer-content-body" style={{ padding: '0 24px 20px', maxHeight: '55vh', overflowY: 'auto' }}>
            {loadingTimeline ? (
              <div style={{ padding: '16px', color: '#94A3B8' }}>Loading audit trail...</div>
            ) : history.length === 0 ? (
              <div style={{ padding: '24px', textAlign: 'center', color: '#64748B' }}>
                No status audit trail found.
              </div>
            ) : (
              <div className="audit-list">
                {history.map((hist, idx) => (
                  <div key={hist.id || idx} style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: '10px 14px',
                    background: 'rgba(15, 23, 42, 0.5)',
                    borderRadius: '6px',
                    marginBottom: '8px',
                    fontSize: '0.8rem'
                  }}>
                    <div>
                      <span className={`status-badge ${hist.status?.toLowerCase().replace(/_/g, '-')}`} style={{ marginRight: '8px' }}>
                        {hist.status}
                      </span>
                      <span style={{ color: '#CBD5E1' }}>{hist.remarks || 'Status transition logged'}</span>
                    </div>
                    <span style={{ color: '#64748B', fontSize: '0.75rem' }}>
                      {hist.created_at ? new Date(hist.created_at).toLocaleString() : ''}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        <div className="modal-actions" style={{ padding: '16px 24px', borderTop: '1px solid rgba(51, 65, 85, 0.8)' }}>
          <button type="button" className="btn-action outline" onClick={onClose}>
            Close Waybill
          </button>
        </div>
      </div>
    </div>
  );
}
