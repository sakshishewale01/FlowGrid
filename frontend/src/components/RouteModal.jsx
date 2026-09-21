import React, { useState, useEffect } from 'react';
import { routesApi } from '../api/routes.js';
import { formatErrorMessage } from '../api/client.js';

/**
 * RouteModal for creating new transit corridors and inspecting route details.
 *
 * @param {Object} props
 * @param {boolean} props.isOpen
 * @param {Function} props.onClose
 * @param {Object|null} props.route - If present, inspection/edit mode; otherwise create mode
 * @param {Function} props.onSaved - Callback after route saved
 */
export default function RouteModal({
  isOpen,
  onClose,
  route = null,
  onSaved,
}) {
  const isEdit = Boolean(route);

  const [formData, setFormData] = useState({
    name: '',
    origin: '',
    destination: '',
    estimated_distance: 500,
    estimated_duration: 8,
    status: 'ACTIVE',
  });

  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [apiError, setApiError] = useState(null);
  const [assignedShipments, setAssignedShipments] = useState([]);
  const [loadingShipments, setLoadingShipments] = useState(false);

  useEffect(() => {
    if (route) {
      setFormData({
        name: route.name || '',
        origin: route.origin || '',
        destination: route.destination || '',
        estimated_distance: route.estimated_distance || 500,
        estimated_duration: route.estimated_duration || 8,
        status: route.status || 'ACTIVE',
      });

      // Load assigned shipments for this route
      setLoadingShipments(true);
      routesApi
        .getRouteShipments(route.id)
        .then((data) => setAssignedShipments(data || []))
        .catch(() => setAssignedShipments([]))
        .finally(() => setLoadingShipments(false));
    } else {
      setFormData({
        name: '',
        origin: '',
        destination: '',
        estimated_distance: 500,
        estimated_duration: 8,
        status: 'ACTIVE',
      });
      setAssignedShipments([]);
    }
    setErrors({});
    setApiError(null);
  }, [route, isOpen]);

  if (!isOpen) return null;

  const validate = () => {
    const errs = {};
    if (!formData.name.trim()) errs.name = 'Route name is required.';
    if (!formData.origin.trim()) errs.origin = 'Origin location is required.';
    if (!formData.destination.trim()) errs.destination = 'Destination location is required.';
    if (!formData.estimated_distance || Number(formData.estimated_distance) < 0) {
      errs.estimated_distance = 'Estimated distance must be >= 0 km.';
    }
    if (!formData.estimated_duration || Number(formData.estimated_duration) < 0) {
      errs.estimated_duration = 'Estimated duration must be >= 0 hours.';
    }
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setApiError(null);
    if (!validate()) return;

    setIsSubmitting(true);
    try {
      const payload = {
        name: formData.name.trim(),
        origin: formData.origin.trim(),
        destination: formData.destination.trim(),
        estimated_distance: Number(formData.estimated_distance),
        estimated_duration: Number(formData.estimated_duration),
        status: formData.status,
      };

      let result;
      if (isEdit) {
        result = await routesApi.updateRoute(route.id, payload);
      } else {
        result = await routesApi.createRoute(payload);
      }

      if (onSaved) onSaved(result, isEdit);
      onClose();
    } catch (err) {
      setApiError(formatErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="modal-backdrop" onClick={onClose} role="dialog" aria-modal="true">
      <div className="modal-card modal-card-large" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-header-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
            </svg>
          </div>
          <div className="modal-header-text">
            <h2 className="modal-title">
              {isEdit ? `Route Details • ${route.name}` : 'Create Transit Corridor'}
            </h2>
            <p className="modal-subtitle">
              {isEdit ? `Corridor #${route.id} between ${route.origin} and ${route.destination}` : 'Define multi-hub transit route corridor and distance parameters'}
            </p>
          </div>
          <button type="button" className="modal-close-btn" onClick={onClose} aria-label="Close modal">×</button>
        </div>

        {/* Informational banner about Automated AI corridor optimization */}
        <div className="optimization-info-banner" style={{
          margin: '0 24px 16px',
          padding: '10px 14px',
          background: 'rgba(59, 130, 246, 0.08)',
          border: '1px solid rgba(59, 130, 246, 0.25)',
          borderRadius: '8px',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          fontSize: '0.8rem',
          color: '#93C5FD'
        }}>
          <span style={{ fontSize: '1.1rem' }}>🤖</span>
          <div>
            <strong>AI Optimization Notice:</strong> Automated multi-stop waypoint optimization & weather rerouting will be activated in upcoming phases. Manual route definition and shipment scheduling are active.
          </div>
        </div>

        {apiError && (
          <div className="auth-alert error" style={{ margin: '0 24px 16px' }} role="alert">
            <div className="auth-alert-content">
              <span className="auth-alert-title">Route Action Failed</span>
              <span className="auth-alert-text">{apiError}</span>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="modal-form">
          <div className="form-group">
            <label className="form-label" htmlFor="route-name">Corridor Name *</label>
            <input
              id="route-name"
              type="text"
              className={`form-input ${errors.name ? 'input-error' : ''}`}
              placeholder="e.g. I-80 Midwest Freight Corridor"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              disabled={isSubmitting}
            />
            {errors.name && <span className="field-error-text">{errors.name}</span>}
          </div>

          <div className="form-row-2">
            <div className="form-group">
              <label className="form-label" htmlFor="route-origin">Origin Terminal / City *</label>
              <input
                id="route-origin"
                type="text"
                className={`form-input ${errors.origin ? 'input-error' : ''}`}
                placeholder="e.g. Chicago Central Hub"
                value={formData.origin}
                onChange={(e) => setFormData({ ...formData, origin: e.target.value })}
                disabled={isSubmitting}
              />
              {errors.origin && <span className="field-error-text">{errors.origin}</span>}
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="route-dest">Destination Terminal / City *</label>
              <input
                id="route-dest"
                type="text"
                className={`form-input ${errors.destination ? 'input-error' : ''}`}
                placeholder="e.g. Dallas Logistics Center"
                value={formData.destination}
                onChange={(e) => setFormData({ ...formData, destination: e.target.value })}
                disabled={isSubmitting}
              />
              {errors.destination && <span className="field-error-text">{errors.destination}</span>}
            </div>
          </div>

          <div className="form-row-3">
            <div className="form-group">
              <label className="form-label" htmlFor="route-dist">Est. Distance (km) *</label>
              <input
                id="route-dist"
                type="number"
                min="0"
                step="0.5"
                className={`form-input ${errors.estimated_distance ? 'input-error' : ''}`}
                value={formData.estimated_distance}
                onChange={(e) => setFormData({ ...formData, estimated_distance: e.target.value })}
                disabled={isSubmitting}
              />
              {errors.estimated_distance && <span className="field-error-text">{errors.estimated_distance}</span>}
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="route-dur">Est. Duration (hours) *</label>
              <input
                id="route-dur"
                type="number"
                min="0"
                step="0.25"
                className={`form-input ${errors.estimated_duration ? 'input-error' : ''}`}
                value={formData.estimated_duration}
                onChange={(e) => setFormData({ ...formData, estimated_duration: e.target.value })}
                disabled={isSubmitting}
              />
              {errors.estimated_duration && <span className="field-error-text">{errors.estimated_duration}</span>}
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="route-status">Corridor Status *</label>
              <select
                id="route-status"
                className="form-input form-select"
                value={formData.status}
                onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                disabled={isSubmitting}
              >
                <option value="ACTIVE">ACTIVE</option>
                <option value="PLANNED">PLANNED</option>
                <option value="COMPLETED">COMPLETED</option>
                <option value="INACTIVE">INACTIVE</option>
              </select>
            </div>
          </div>

          {/* If inspecting an existing route, show assigned shipments */}
          {isEdit && (
            <div className="route-shipments-section" style={{ marginTop: '16px' }}>
              <h4 style={{ fontSize: '0.85rem', color: '#E2E8F0', marginBottom: '8px', fontWeight: 600 }}>
                Assigned Shipments ({assignedShipments.length})
              </h4>
              {loadingShipments ? (
                <div style={{ color: '#94A3B8', fontSize: '0.82rem', padding: '12px' }}>Loading shipments...</div>
              ) : assignedShipments.length === 0 ? (
                <div style={{ color: '#64748B', fontSize: '0.82rem', padding: '12px', background: 'rgba(15, 23, 42, 0.4)', borderRadius: '6px' }}>
                  No shipments currently allocated to this route corridor.
                </div>
              ) : (
                <div className="assigned-shipments-mini-list" style={{ maxHeight: '140px', overflowY: 'auto' }}>
                  {assignedShipments.map((s) => (
                    <div key={s.id} style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '8px 12px',
                      background: 'rgba(15, 23, 42, 0.5)',
                      borderRadius: '6px',
                      marginBottom: '6px',
                      fontSize: '0.8rem'
                    }}>
                      <span style={{ fontFamily: 'monospace', color: '#38BDF8' }}>{s.tracking_number}</span>
                      <span style={{ color: '#94A3B8' }}>{s.destination_city}, {s.destination_state}</span>
                      <span className="status-badge" style={{ fontSize: '0.7rem' }}>{s.status}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          <div className="modal-actions">
            <button
              type="button"
              className="btn-action outline"
              onClick={onClose}
              disabled={isSubmitting}
            >
              Close
            </button>
            <button
              type="submit"
              className="btn-action primary"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Saving...' : isEdit ? 'Update Route' : 'Create Route'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
