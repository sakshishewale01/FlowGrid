import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { shipmentsApi } from '../api/shipments.js';
import { trackingApi } from '../api/tracking.js';
import { driversApi } from '../api/drivers.js';
import { vehiclesApi } from '../api/vehicles.js';
import { formatErrorMessage } from '../api/client.js';
import StatusBadge from './StatusBadge';
import ConfirmDialog from './ConfirmDialog';
import ShipmentRouteMap from './ShipmentRouteMap';
import useTrackingWebSocket, { WS_STATUS } from '../hooks/useTrackingWebSocket.js';
import { useNotifications } from '../context/NotificationContext';



/**
 * Adheres strictly to backend ALLOWED_TRANSITIONS state machine rules:
 * CREATED -> CONFIRMED, CANCELLED
 * CONFIRMED -> ASSIGNED, CANCELLED
 * ASSIGNED -> PICKED_UP, CANCELLED
 * PICKED_UP -> IN_TRANSIT
 * IN_TRANSIT -> OUT_FOR_DELIVERY
 * OUT_FOR_DELIVERY -> DELIVERED, FAILED
 * FAILED -> OUT_FOR_DELIVERY, RETURNED
 */

const WORKFLOW_STAGES = [
  'CREATED',
  'CONFIRMED',
  'ASSIGNED',
  'PICKED_UP',
  'IN_TRANSIT',
  'OUT_FOR_DELIVERY',
  'DELIVERED',
];

export default function ShipmentDetailDrawer({
  isOpen,
  onClose,
  shipment = null,
  onUpdated,
}) {
  const { user, token: authToken } = useAuth();

  const { toast } = useToast();
  const { notifyShipmentStatus } = useNotifications();
  const isAuthorized = user?.role === 'ADMIN' || user?.role === 'MANAGER';


  const [activeTab, setActiveTab] = useState('overview'); // 'overview' | 'tracking' | 'history'
  const [history, setHistory] = useState([]);
  const [events, setEvents] = useState([]);
  const [latestTracking, setLatestTracking] = useState(null);
  const [loadingTimeline, setLoadingTimeline] = useState(false);
  const [timelineError, setTimelineError] = useState(null);
  const [isPolling, setIsPolling] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Available drivers & vehicles for assignment
  const [drivers, setDrivers] = useState([]);
  const [vehicles, setVehicles] = useState([]);
  const [selectedDriverId, setSelectedDriverId] = useState('');
  const [selectedVehicleId, setSelectedVehicleId] = useState('');
  const [isAssigning, setIsAssigning] = useState(false);
  const [showAssignPanel, setShowAssignPanel] = useState(false);

  // Status transition state
  const [statusRemarks, setStatusRemarks] = useState('');
  const [isUpdatingStatus, setIsUpdatingStatus] = useState(false);
  const [statusError, setStatusError] = useState(null);

  // Add event state
  const [eventLocation, setEventLocation] = useState('');
  const [eventNotes, setEventNotes] = useState('');
  const [isAddingEvent, setIsAddingEvent] = useState(false);
  const [eventError, setEventError] = useState(null);

  // Cancel Confirmation dialog state
  const [isCancelConfirmOpen, setIsCancelConfirmOpen] = useState(false);
  const [isCancelling, setIsCancelling] = useState(false);

  const loadTimelineData = useCallback(async (shipmentId, showLoadingSpinner = true) => {
    if (showLoadingSpinner) {
      setLoadingTimeline(true);
    }
    setTimelineError(null);
    try {
      const [histData, evData, latestData] = await Promise.allSettled([
        trackingApi.getStatusHistory(shipmentId),
        trackingApi.getTrackingEvents(shipmentId),
        trackingApi.getLatestTrackingInfo(shipmentId),
      ]);

      if (histData.status === 'fulfilled') {
        setHistory(histData.value || []);
      }
      if (evData.status === 'fulfilled') {
        setEvents(evData.value || []);
      }
      if (latestData.status === 'fulfilled') {
        setLatestTracking(latestData.value || null);
      }
    } catch (err) {
      setTimelineError(formatErrorMessage(err));
    } finally {
      if (showLoadingSpinner) {
        setLoadingTimeline(false);
      }
    }
  }, []);

  // Fetch drivers and vehicles when drawer opens
  useEffect(() => {
    if (isOpen) {
      driversApi.listDrivers({ limit: 100 })
        .then((data) => setDrivers(data || []))
        .catch(() => {});

      vehiclesApi.listVehicles({ limit: 100 })
        .then((data) => setVehicles(data || []))
        .catch(() => {});
    }
  }, [isOpen]);

  useEffect(() => {
    if (shipment && isOpen) {
      loadTimelineData(shipment.id);
      setSelectedDriverId(shipment.assigned_driver_id ? String(shipment.assigned_driver_id) : '');
      setSelectedVehicleId(shipment.assigned_vehicle_id ? String(shipment.assigned_vehicle_id) : '');
      setStatusRemarks('');
      setEventLocation('');
      setEventNotes('');
      setStatusError(null);
      setEventError(null);
      setShowAssignPanel(false);
    }
  }, [shipment, isOpen, loadTimelineData]);

  // Polling interval (15s) when live polling is active
  useEffect(() => {
    if (!isOpen || !shipment?.id || !isPolling) return;
    const interval = setInterval(() => {
      loadTimelineData(shipment.id, false);
    }, 15000);
    return () => clearInterval(interval);
  }, [isOpen, shipment?.id, isPolling, loadTimelineData]);

  // Real-time WebSocket Event Handler
  const handleWsEvent = useCallback(
    (event) => {
      if (!shipment?.id) return;
      if (event.event === 'STATUS_UPDATED') {
        loadTimelineData(shipment.id, false);
        if (onUpdated) {
          onUpdated({
            ...shipment,
            status: event.data?.status || shipment.status,
          });
        }
        if (notifyShipmentStatus) {
          notifyShipmentStatus({
            shipmentId: shipment.id,
            trackingNumber: shipment.tracking_number,
            status: event.data?.status || shipment.status,
            remarks: event.data?.remarks,
          });
        }
        toast.info(
          `Live Update: Status changed to ${event.data?.status?.replace(/_/g, ' ') || 'New Status'}`
        );

      } else if (event.event === 'TRACKING_EVENT_ADDED') {
        loadTimelineData(shipment.id, false);
        toast.info(
          `Live Checkpoint: ${event.data?.location || 'New checkpoint recorded'}`
        );
      } else if (event.event === 'SHIPMENT_UPDATED') {
        loadTimelineData(shipment.id, false);
        if (onUpdated) {
          onUpdated({
            ...shipment,
            assigned_driver_id:
              event.data?.assigned_driver_id ?? shipment.assigned_driver_id,
            assigned_vehicle_id:
              event.data?.assigned_vehicle_id ?? shipment.assigned_vehicle_id,
          });
        }
      }
    },
    [shipment, loadTimelineData, onUpdated, toast, notifyShipmentStatus]
  );


  // Connect tracking WebSocket
  const {
    connectionStatus,
    errorDetail: wsErrorDetail,
    reconnect: reconnectWs,
  } = useTrackingWebSocket({
    shipmentId: shipment?.id,
    token: authToken,
    enabled: isOpen && Boolean(shipment?.id),
    onEvent: handleWsEvent,
  });


  // Manual refresh handler
  const handleRefreshTracking = async () => {
    if (!shipment?.id) return;
    setIsRefreshing(true);
    try {
      await loadTimelineData(shipment.id, true);
      toast.success('Live tracking telemetry refreshed');
    } catch {
      toast.error('Failed to refresh tracking data');
    } finally {
      setIsRefreshing(false);
    }
  };


  if (!isOpen || !shipment) return null;

  const currentStatus = shipment.status;
  const isTerminal = ['DELIVERED', 'CANCELLED', 'RETURNED'].includes(currentStatus);
  const stageIndex = WORKFLOW_STAGES.indexOf(currentStatus);

  // Status transition execution
  const executeTransition = async (nextStatus, customRemarks) => {
    setIsUpdatingStatus(true);
    setStatusError(null);
    try {
      const updated = await shipmentsApi.transitionStatus(shipment.id, {
        status: nextStatus,
        remarks: customRemarks || statusRemarks.trim() || undefined,
      });

      toast.success(`Shipment advanced to ${nextStatus.replace(/_/g, ' ')}`);
      if (notifyShipmentStatus) {
        notifyShipmentStatus({
          shipmentId: shipment.id,
          trackingNumber: shipment.tracking_number,
          status: nextStatus,
          remarks: customRemarks || statusRemarks.trim() || undefined,
        });
      }
      if (onUpdated) onUpdated(updated);
      loadTimelineData(shipment.id);
      setStatusRemarks('');

    } catch (err) {
      const errMsg = formatErrorMessage(err);
      setStatusError(errMsg);
      toast.error(errMsg);
    } finally {
      setIsUpdatingStatus(false);
    }
  };

  // Driver & Vehicle assignment execution
  const handleAssignResources = async (e) => {
    e.preventDefault();
    if (!selectedDriverId || !selectedVehicleId) {
      setStatusError('Please select both a driver and a vehicle for assignment.');
      return;
    }

    setIsAssigning(true);
    setStatusError(null);
    try {
      // 1. Assign driver and vehicle IDs via shipment update
      await shipmentsApi.assignShipment(shipment.id, {
        driver_id: Number(selectedDriverId),
        vehicle_id: Number(selectedVehicleId),
      });

      // 2. If status is CONFIRMED, transition directly to ASSIGNED
      let updated = shipment;
      if (currentStatus === 'CONFIRMED') {
        updated = await shipmentsApi.transitionStatus(shipment.id, {
          status: 'ASSIGNED',
          remarks: `Assigned to Driver #${selectedDriverId} and Vehicle #${selectedVehicleId}`,
        });
      } else {
        // Refetch updated shipment details
        updated = await shipmentsApi.getShipment(shipment.id);
      }

      toast.success('Driver and vehicle assigned successfully');
      setShowAssignPanel(false);
      if (onUpdated) onUpdated(updated);
      loadTimelineData(shipment.id);
    } catch (err) {
      const msg = formatErrorMessage(err);
      setStatusError(msg);
      toast.error(msg);
    } finally {
      setIsAssigning(false);
    }
  };

  // Cancel order execution
  const handleConfirmCancel = async () => {
    setIsCancelling(true);
    try {
      const updated = await shipmentsApi.transitionStatus(shipment.id, {
        status: 'CANCELLED',
        remarks: 'Order cancelled by dispatch operator',
      });
      toast.warning('Shipment order has been cancelled');
      setIsCancelConfirmOpen(false);
      if (onUpdated) onUpdated(updated);
      loadTimelineData(shipment.id);
    } catch (err) {
      toast.error(formatErrorMessage(err));
    } finally {
      setIsCancelling(false);
    }
  };

  // Add waypoint checkpoint
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
      toast.success('Waypoint checkpoint logged');
      setEventLocation('');
      setEventNotes('');
      loadTimelineData(shipment.id);
    } catch (err) {
      const msg = formatErrorMessage(err);
      setEventError(msg);
      toast.error(msg);
    } finally {
      setIsAddingEvent(false);
    }
  };

  return (
    <>
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
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
                <h2 className="modal-title" style={{ fontFamily: 'monospace', letterSpacing: '0.04em' }}>
                  {shipment.tracking_number}
                </h2>
                <StatusBadge status={shipment.status} />
                <span
                  className={`ws-header-pill ${connectionStatus.toLowerCase()}`}
                  title={
                    connectionStatus === WS_STATUS.CONNECTED
                      ? 'Live real-time WebSocket connection active'
                      : connectionStatus === WS_STATUS.CONNECTING
                      ? 'Connecting live tracking socket...'
                      : connectionStatus === WS_STATUS.ERROR
                      ? `WebSocket error: ${wsErrorDetail || 'Connection failed'}. Click to reconnect.`
                      : 'WebSocket disconnected. Click to reconnect.'
                  }
                  onClick={connectionStatus !== WS_STATUS.CONNECTED ? reconnectWs : undefined}
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '5px',
                    padding: '2px 8px',
                    borderRadius: '10px',
                    fontSize: '0.70rem',
                    fontWeight: 600,
                    cursor: connectionStatus !== WS_STATUS.CONNECTED ? 'pointer' : 'default',
                    background:
                      connectionStatus === WS_STATUS.CONNECTED
                        ? 'rgba(16, 185, 129, 0.15)'
                        : connectionStatus === WS_STATUS.CONNECTING
                        ? 'rgba(234, 179, 8, 0.15)'
                        : connectionStatus === WS_STATUS.ERROR
                        ? 'rgba(239, 68, 68, 0.15)'
                        : 'rgba(100, 116, 139, 0.15)',
                    color:
                      connectionStatus === WS_STATUS.CONNECTED
                        ? '#10B981'
                        : connectionStatus === WS_STATUS.CONNECTING
                        ? '#EAB308'
                        : connectionStatus === WS_STATUS.ERROR
                        ? '#EF4444'
                        : '#94A3B8',
                    border: `1px solid ${
                      connectionStatus === WS_STATUS.CONNECTED
                        ? 'rgba(16, 185, 129, 0.3)'
                        : connectionStatus === WS_STATUS.CONNECTING
                        ? 'rgba(234, 179, 8, 0.3)'
                        : connectionStatus === WS_STATUS.ERROR
                        ? 'rgba(239, 68, 68, 0.3)'
                        : 'rgba(100, 116, 139, 0.3)'
                    }`,
                  }}
                >
                  <span
                    style={{
                      width: '6px',
                      height: '6px',
                      borderRadius: '50%',
                      backgroundColor: 'currentColor',
                    }}
                  />
                  <span>
                    {connectionStatus === WS_STATUS.CONNECTED
                      ? 'Live'
                      : connectionStatus === WS_STATUS.CONNECTING
                      ? 'Connecting...'
                      : connectionStatus === WS_STATUS.ERROR
                      ? 'WS Error'
                      : 'Offline'}
                  </span>
                </span>
              </div>

              <p className="modal-subtitle">
                Manifest #{shipment.id} • Registered {shipment.created_at ? new Date(shipment.created_at).toLocaleDateString() : 'Active'}
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
              End-to-End Workflow
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
              Route & Live Tracking ({events.length})
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
              Audit Trail ({history.length})
            </button>
          </div>

          {/* TAB 1: End-to-End Workflow & Details */}
          {activeTab === 'overview' && (
            <div className="drawer-content-body" style={{ padding: '0 24px 20px', maxHeight: '58vh', overflowY: 'auto' }}>
              {/* Stepper Progress Bar */}
              <div className="workflow-stepper-panel" style={{
                padding: '16px',
                background: 'rgba(15, 23, 42, 0.7)',
                border: '1px solid rgba(51, 65, 85, 0.8)',
                borderRadius: '8px',
                marginBottom: '18px'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                  <span style={{ fontSize: '0.78rem', color: '#94A3B8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    Logistics Lifecycle Stage
                  </span>
                  <span style={{ fontSize: '0.8rem', fontWeight: 600, color: isTerminal ? '#94A3B8' : '#38BDF8' }}>
                    {isTerminal ? currentStatus : `Stage ${stageIndex + 1} of ${WORKFLOW_STAGES.length}`}
                  </span>
                </div>

                <div className="stepper-bar-track" style={{ display: 'flex', gap: '4px', height: '6px', borderRadius: '3px', overflow: 'hidden', background: 'rgba(255, 255, 255, 0.08)' }}>
                  {WORKFLOW_STAGES.map((st, i) => {
                    const isDone = stageIndex >= i;
                    const isCurrent = currentStatus === st;
                    return (
                      <div
                        key={st}
                        style={{
                          flex: 1,
                          background: currentStatus === 'CANCELLED' || currentStatus === 'RETURNED'
                            ? '#64748B'
                            : isCurrent
                            ? '#38BDF8'
                            : isDone
                            ? '#10B981'
                            : 'transparent',
                          transition: 'background 0.3s ease'
                        }}
                        title={st}
                      />
                    );
                  })}
                </div>
              </div>

              {/* Waybill Details Matrix */}
              <div className="manifest-grid-2" style={{ marginBottom: '18px' }}>
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
                  <span className="manifest-sub">{shipment.assigned_driver?.phone_number || 'Mobile contact pending'}</span>
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
                  <span className="manifest-label">Payload Weight & Volume</span>
                  <span className="manifest-value">{shipment.total_weight_kg ? `${shipment.total_weight_kg} kg` : '0 kg'}</span>
                  <span className="manifest-sub">{shipment.total_volume_cbm ? `${shipment.total_volume_cbm} m³` : 'Standard freight'}</span>
                </div>

                <div className="manifest-item">
                  <span className="manifest-label">Scheduled Pickup Window</span>
                  <span className="manifest-value">
                    {shipment.scheduled_pickup_at ? new Date(shipment.scheduled_pickup_at).toLocaleString() : 'Immediate Dispatch'}
                  </span>
                  <span className="manifest-sub">
                    {shipment.delivered_at ? `Delivered: ${new Date(shipment.delivered_at).toLocaleString()}` : 'In Service'}
                  </span>
                </div>
              </div>

              {/* Interactive Workflow Action Center */}
              <div className="workflow-action-center" style={{
                padding: '16px',
                background: 'rgba(15, 23, 42, 0.8)',
                border: '1px solid rgba(56, 189, 248, 0.3)',
                borderRadius: '8px'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                  <h4 style={{ fontSize: '0.875rem', fontWeight: 600, color: '#F8FAFC', margin: 0 }}>
                    Workflow Action Center
                  </h4>
                  {!isTerminal && (
                    <span style={{ fontSize: '0.75rem', color: '#94A3B8' }}>
                      Next permitted action based on status <strong>{currentStatus}</strong>
                    </span>
                  )}
                </div>

                {statusError && (
                  <div className="auth-alert error" style={{ marginBottom: '12px' }}>
                    <span className="auth-alert-text">{statusError}</span>
                  </div>
                )}

                {!isAuthorized ? (
                  <p style={{ fontSize: '0.8rem', color: '#94A3B8', margin: 0 }}>
                    🔒 Workflow execution and status transitions require ADMIN or MANAGER privileges. (Your role: {user?.role})
                  </p>
                ) : isTerminal ? (
                  <div style={{ padding: '8px 0', color: '#10B981', fontSize: '0.825rem' }}>
                    ✓ Order reached terminal status <strong>{currentStatus}</strong>. Historical record preserved.
                  </div>
                ) : (
                  <div className="workflow-action-buttons" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {/* Step 1: Confirm Shipment */}
                    {currentStatus === 'CREATED' && (
                      <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                        <button
                          type="button"
                          className="btn-action primary"
                          disabled={isUpdatingStatus}
                          onClick={() => executeTransition('CONFIRMED', 'Order confirmed by logistics planner')}
                        >
                          ✓ Confirm Shipment
                        </button>
                        <span style={{ fontSize: '0.78rem', color: '#94A3B8' }}>
                          Validates route and prepares order for resource assignment.
                        </span>
                      </div>
                    )}

                    {/* Step 2: Resource Allocation Panel (Driver & Vehicle) */}
                    {(currentStatus === 'CONFIRMED' || currentStatus === 'CREATED') && (
                      <div style={{
                        padding: '12px',
                        background: 'rgba(30, 41, 59, 0.6)',
                        border: '1px solid rgba(51, 65, 85, 0.7)',
                        borderRadius: '6px'
                      }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                          <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#E2E8F0' }}>
                            {shipment.assigned_driver_id ? 'Reassign Driver & Vehicle' : 'Assign Driver & Vehicle'}
                          </span>
                          <button
                            type="button"
                            className="btn-action outline"
                            style={{ padding: '2px 8px', fontSize: '0.72rem' }}
                            onClick={() => setShowAssignPanel(!showAssignPanel)}
                          >
                            {showAssignPanel ? 'Hide Form' : 'Select Resources'}
                          </button>
                        </div>

                        {showAssignPanel && (
                          <form onSubmit={handleAssignResources}>
                            <div className="form-row-2">
                              <div className="form-group" style={{ marginBottom: '8px' }}>
                                <label className="form-label" style={{ fontSize: '0.75rem' }}>Select Driver *</label>
                                <select
                                  className="form-input form-select"
                                  style={{ fontSize: '0.8rem' }}
                                  value={selectedDriverId}
                                  onChange={(e) => setSelectedDriverId(e.target.value)}
                                  disabled={isAssigning}
                                >
                                  <option value="">-- Choose Driver --</option>
                                  {drivers.map((d) => (
                                    <option key={d.id} value={d.id}>
                                      Driver #{d.id} ({d.license_number}) — {d.availability_status}
                                    </option>
                                  ))}
                                </select>
                              </div>

                              <div className="form-group" style={{ marginBottom: '8px' }}>
                                <label className="form-label" style={{ fontSize: '0.75rem' }}>Select Fleet Vehicle *</label>
                                <select
                                  className="form-input form-select"
                                  style={{ fontSize: '0.8rem' }}
                                  value={selectedVehicleId}
                                  onChange={(e) => setSelectedVehicleId(e.target.value)}
                                  disabled={isAssigning}
                                >
                                  <option value="">-- Choose Vehicle --</option>
                                  {vehicles.map((v) => (
                                    <option key={v.id} value={v.id}>
                                      {v.registration_number} ({v.vehicle_type} - {v.capacity}kg) — {v.status}
                                    </option>
                                  ))}
                                </select>
                              </div>
                            </div>

                            <button
                              type="submit"
                              className="btn-action primary"
                              style={{ fontSize: '0.78rem', padding: '6px 14px' }}
                              disabled={isAssigning}
                            >
                              {isAssigning ? 'Assigning...' : currentStatus === 'CONFIRMED' ? 'Assign & Advance to ASSIGNED' : 'Save Resource Assignment'}
                            </button>
                          </form>
                        )}
                      </div>
                    )}

                    {/* Step 3: Dispatch & Pick Up Freight */}
                    {currentStatus === 'ASSIGNED' && (
                      <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                        <button
                          type="button"
                          className="btn-action primary"
                          disabled={isUpdatingStatus}
                          onClick={() => executeTransition('PICKED_UP', 'Cargo picked up from depot dock')}
                        >
                          🚛 Dispatch & Pick Up Cargo
                        </button>
                        <span style={{ fontSize: '0.78rem', color: '#94A3B8' }}>
                          Driver departs origin warehouse loading bay.
                        </span>
                      </div>
                    )}

                    {/* Step 4: Mark In Transit */}
                    {currentStatus === 'PICKED_UP' && (
                      <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                        <button
                          type="button"
                          className="btn-action primary"
                          disabled={isUpdatingStatus}
                          onClick={() => executeTransition('IN_TRANSIT', 'Freight traveling along main corridor')}
                        >
                          🛣️ Mark In Transit
                        </button>
                        <span style={{ fontSize: '0.78rem', color: '#94A3B8' }}>
                          Activates real-time freight corridor transit.
                        </span>
                      </div>
                    )}

                    {/* Step 5: Out for Delivery */}
                    {currentStatus === 'IN_TRANSIT' && (
                      <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                        <button
                          type="button"
                          className="btn-action primary"
                          disabled={isUpdatingStatus}
                          onClick={() => executeTransition('OUT_FOR_DELIVERY', 'Arrived at destination zone, out for delivery')}
                        >
                          📦 Out for Final Delivery
                        </button>
                        <span style={{ fontSize: '0.78rem', color: '#94A3B8' }}>
                          Vehicle dispatched on last-mile route.
                        </span>
                      </div>
                    )}

                    {/* Step 6: Complete Delivery or Record Failure */}
                    {currentStatus === 'OUT_FOR_DELIVERY' && (
                      <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
                        <button
                          type="button"
                          className="btn-action primary"
                          disabled={isUpdatingStatus}
                          onClick={() => executeTransition('DELIVERED', 'Consignee received and signed cargo')}
                        >
                          ✓ Confirm Delivery Succeeded
                        </button>
                        <button
                          type="button"
                          className="btn-action outline"
                          style={{ borderColor: 'rgba(239, 68, 68, 0.4)', color: '#F87171' }}
                          disabled={isUpdatingStatus}
                          onClick={() => executeTransition('FAILED', 'Consignee unavailable / delivery attempt failed')}
                        >
                          ✕ Record Delivery Failure
                        </button>
                      </div>
                    )}

                    {/* Step 7: Failed State Recovery */}
                    {currentStatus === 'FAILED' && (
                      <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                        <button
                          type="button"
                          className="btn-action primary"
                          disabled={isUpdatingStatus}
                          onClick={() => executeTransition('OUT_FOR_DELIVERY', 'Re-attempting delivery to consignee')}
                        >
                          🔄 Re-attempt Delivery
                        </button>
                        <button
                          type="button"
                          className="btn-action outline"
                          style={{ borderColor: 'rgba(239, 68, 68, 0.4)', color: '#F87171' }}
                          disabled={isUpdatingStatus}
                          onClick={() => executeTransition('RETURNED', 'Cargo returned to distribution hub')}
                        >
                          ↩ Return Cargo to Depot
                        </button>
                      </div>
                    )}

                    {/* Order Cancellation (Allowed for any active non-terminal state) */}
                    <div style={{ marginTop: '8px', paddingTop: '10px', borderTop: '1px solid rgba(51, 65, 85, 0.5)', display: 'flex', justifyContent: 'flex-end' }}>
                      <button
                        type="button"
                        className="btn-action outline"
                        style={{ borderColor: 'rgba(239, 68, 68, 0.3)', color: '#F87171', fontSize: '0.75rem', padding: '4px 10px' }}
                        onClick={() => setIsCancelConfirmOpen(true)}
                        disabled={isUpdatingStatus}
                      >
                        Cancel Shipment
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 2: Route & Live Tracking */}
          {activeTab === 'tracking' && (
            <div className="drawer-content-body" style={{ padding: '0 24px 20px', maxHeight: '58vh', overflowY: 'auto' }}>
              {/* Telemetry Control Bar */}
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '14px',
                flexWrap: 'wrap',
                gap: '8px'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#F1F5F9' }}>
                    Telemetry & Freight Corridor
                  </span>
                  {/* Real-time WebSocket Status Pill */}
                  <button
                    type="button"
                    className={`ws-control-pill ${connectionStatus.toLowerCase()}`}
                    onClick={connectionStatus !== WS_STATUS.CONNECTED ? reconnectWs : undefined}
                    title={
                      connectionStatus === WS_STATUS.CONNECTED
                        ? 'FastAPI WebSocket connected'
                        : connectionStatus === WS_STATUS.CONNECTING
                        ? 'Connecting to /ws/tracking...'
                        : connectionStatus === WS_STATUS.ERROR
                        ? `WebSocket Error: ${wsErrorDetail || 'Failed'}. Click to retry.`
                        : 'WebSocket disconnected. Click to reconnect.'
                    }
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '6px',
                      padding: '4px 10px',
                      borderRadius: '16px',
                      fontSize: '0.74rem',
                      fontWeight: 600,
                      cursor: connectionStatus !== WS_STATUS.CONNECTED ? 'pointer' : 'default',
                      background:
                        connectionStatus === WS_STATUS.CONNECTED
                          ? 'rgba(16, 185, 129, 0.15)'
                          : connectionStatus === WS_STATUS.CONNECTING
                          ? 'rgba(234, 179, 8, 0.15)'
                          : connectionStatus === WS_STATUS.ERROR
                          ? 'rgba(239, 68, 68, 0.15)'
                          : 'rgba(100, 116, 139, 0.15)',
                      color:
                        connectionStatus === WS_STATUS.CONNECTED
                          ? '#10B981'
                          : connectionStatus === WS_STATUS.CONNECTING
                          ? '#EAB308'
                          : connectionStatus === WS_STATUS.ERROR
                          ? '#EF4444'
                          : '#94A3B8',
                      border: `1px solid ${
                        connectionStatus === WS_STATUS.CONNECTED
                          ? 'rgba(16, 185, 129, 0.35)'
                          : connectionStatus === WS_STATUS.CONNECTING
                          ? 'rgba(234, 179, 8, 0.35)'
                          : connectionStatus === WS_STATUS.ERROR
                          ? 'rgba(239, 68, 68, 0.35)'
                          : 'rgba(100, 116, 139, 0.35)'
                      }`,
                    }}
                  >
                    <span
                      style={{
                        width: '7px',
                        height: '7px',
                        borderRadius: '50%',
                        backgroundColor: 'currentColor',
                      }}
                    />
                    <span>
                      {connectionStatus === WS_STATUS.CONNECTED
                        ? '⚡ Live WS: Connected'
                        : connectionStatus === WS_STATUS.CONNECTING
                        ? '⚡ Live WS: Connecting...'
                        : connectionStatus === WS_STATUS.ERROR
                        ? '⚡ Live WS: Error'
                        : '⚡ Live WS: Disconnected'}
                    </span>
                  </button>
                  <button
                    type="button"
                    className={`poll-toggle-pill ${isPolling ? 'active' : ''}`}
                    onClick={() => setIsPolling(!isPolling)}
                    title="Toggle automatic 15-second live telemetry refresh"
                  >
                    <span className="poll-pulse-dot" />
                    <span>{isPolling ? 'Live Polling: 15s' : 'Enable Live Polling'}</span>
                  </button>

                </div>

                <button
                  type="button"
                  className="fg-export-btn"
                  style={{ padding: '4px 10px', fontSize: '0.75rem' }}
                  onClick={handleRefreshTracking}
                  disabled={isRefreshing || loadingTimeline}
                  title="Force refresh status and waypoints"
                >
                  <svg
                    width="14"
                    height="14"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2.5"
                    className={isRefreshing ? 'rotating-spin' : ''}
                  >
                    <polyline points="23 4 23 10 17 10" />
                    <polyline points="1 20 1 14 7 14" />
                    <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
                  </svg>
                  <span>{isRefreshing ? 'Refreshing...' : 'Refresh'}</span>
                </button>
              </div>

              {/* Telemetry Cards Grid */}
              <div className="telemetry-card-grid">
                <div className="telemetry-card">
                  <span className="telemetry-card-label">Current Position / Hub</span>
                  <span className="telemetry-card-value">
                    {latestTracking?.latest_event?.location || events[0]?.location || (shipment.origin_warehouse ? shipment.origin_warehouse.name : 'Origin Dispatch')}
                  </span>
                  <span className="telemetry-card-sub">
                    {latestTracking?.latest_event?.event_type || 'ORIGIN DEPOSIT'}
                  </span>
                </div>

                <div className="telemetry-card">
                  <span className="telemetry-card-label">Latest Milestone</span>
                  <span className="telemetry-card-value" style={{ fontSize: '0.82rem' }}>
                    {latestTracking?.latest_event?.description || events[0]?.description || 'Shipment registered in FlowGrid network'}
                  </span>
                  <span className="telemetry-card-sub">
                    {latestTracking?.latest_event?.timestamp
                      ? new Date(latestTracking.latest_event.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
                      : 'Initial creation'}
                  </span>
                </div>

                <div className="telemetry-card">
                  <span className="telemetry-card-label">Transit State</span>
                  <div style={{ marginTop: '2px' }}>
                    <StatusBadge status={shipment.status} />
                  </div>
                  <span className="telemetry-card-sub" style={{ marginTop: '4px' }}>
                    {events.length} logged waypoint{events.length !== 1 ? 's' : ''}
                  </span>
                </div>
              </div>

              {/* Interactive Route Map */}
              <div style={{ marginBottom: '18px' }}>
                <ShipmentRouteMap shipment={shipment} trackingEvents={events} height="300px" />
              </div>

              {/* Record Physical Waypoint Form */}
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
                          placeholder="Location (e.g. Toledo Transit Point, OH or 41.65, -83.53)"
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

              {/* Waypoint Chronological Checkpoints */}
              {loadingTimeline && !isPolling ? (
                <div style={{ padding: '16px', color: '#94A3B8' }}>Loading waypoint history...</div>
              ) : events.length === 0 ? (
                <div style={{ padding: '20px', textAlign: 'center', color: '#64748B', background: 'rgba(15, 23, 42, 0.4)', borderRadius: '6px' }}>
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
                        marginTop: '6px',
                        boxShadow: '0 0 8px rgba(56, 189, 248, 0.6)'
                      }} />
                      <div style={{ flex: 1 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <span style={{ fontSize: '0.85rem', color: '#F1F5F9', fontWeight: 600 }}>
                            {ev.location}
                          </span>
                          <span style={{ fontSize: '0.72rem', color: '#64748B', fontFamily: 'monospace' }}>
                            {ev.timestamp ? new Date(ev.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}
                          </span>
                        </div>
                        <div style={{ fontSize: '0.75rem', color: '#94A3B8', marginTop: '2px' }}>
                          {ev.timestamp ? new Date(ev.timestamp).toLocaleDateString() : 'Checkpoint logged'}
                          {ev.description && ` • "${ev.description}"`}
                          {ev.notes && ` • "${ev.notes}"`}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* TAB 3: Status Audit Trail */}
          {activeTab === 'history' && (
            <div className="drawer-content-body" style={{ padding: '0 24px 20px', maxHeight: '58vh', overflowY: 'auto' }}>
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
                        <StatusBadge status={hist.new_status} size="small" style={{ marginRight: '8px' }} />
                        <span style={{ color: '#CBD5E1', marginLeft: '8px' }}>{hist.remarks || 'Status transition logged'}</span>
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

      {/* Confirmation Dialog for Destructive Cancellation */}
      <ConfirmDialog
        isOpen={isCancelConfirmOpen}
        title="Cancel Shipment Order"
        message={`Are you sure you want to cancel shipment ${shipment.tracking_number}? This transitions the manifest to terminal CANCELLED state.`}
        confirmLabel="Yes, Cancel Shipment"
        cancelLabel="Keep Active"
        confirmVariant="danger"
        isLoading={isCancelling}
        onConfirm={handleConfirmCancel}
        onCancel={() => setIsCancelConfirmOpen(false)}
      />
    </>
  );
}
