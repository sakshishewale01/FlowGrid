import React, { useState, useEffect } from 'react';
import { vehiclesApi } from '../api/vehicles.js';
import { formatErrorMessage } from '../api/client.js';

/**
 * VehicleModal for registering fleet vehicles or modifying vehicle attributes/status.
 *
 * @param {Object} props
 * @param {boolean} props.isOpen
 * @param {Function} props.onClose
 * @param {Object|null} props.vehicle
 * @param {boolean} props.isStatusOnly
 * @param {Function} props.onSaved
 */
export default function VehicleModal({
  isOpen,
  onClose,
  vehicle = null,
  isStatusOnly = false,
  onSaved,
}) {
  const isEdit = Boolean(vehicle);

  const [formData, setFormData] = useState({
    registration_number: '',
    vehicle_type: 'Box Truck',
    capacity: 10000,
    status: 'AVAILABLE',
  });

  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [apiError, setApiError] = useState(null);

  useEffect(() => {
    if (vehicle) {
      setFormData({
        registration_number: vehicle.registration_number || '',
        vehicle_type: vehicle.vehicle_type || 'Box Truck',
        capacity: vehicle.capacity || 10000,
        status: vehicle.status || 'AVAILABLE',
      });
    } else {
      setFormData({
        registration_number: '',
        vehicle_type: 'Box Truck',
        capacity: 10000,
        status: 'AVAILABLE',
      });
    }
    setErrors({});
    setApiError(null);
  }, [vehicle, isOpen]);

  if (!isOpen) return null;

  const validate = () => {
    const errs = {};
    if (!isStatusOnly) {
      if (!formData.registration_number.trim() || formData.registration_number.trim().length < 2) {
        errs.registration_number = 'Registration / license plate must be at least 2 characters.';
      }
      if (!formData.vehicle_type.trim() || formData.vehicle_type.trim().length < 2) {
        errs.vehicle_type = 'Vehicle type is required.';
      }
      if (!formData.capacity || Number(formData.capacity) <= 0) {
        errs.capacity = 'Capacity must be greater than 0 kg.';
      }
    }
    if (!formData.status) {
      errs.status = 'Status is required.';
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
      let result;
      if (isStatusOnly && vehicle) {
        result = await vehiclesApi.updateVehicle(vehicle.id, {
          status: formData.status,
        });
      } else if (isEdit) {
        result = await vehiclesApi.updateVehicle(vehicle.id, {
          registration_number: formData.registration_number.trim(),
          vehicle_type: formData.vehicle_type.trim(),
          capacity: Number(formData.capacity),
          status: formData.status,
        });
      } else {
        result = await vehiclesApi.createVehicle({
          registration_number: formData.registration_number.trim(),
          vehicle_type: formData.vehicle_type.trim(),
          capacity: Number(formData.capacity),
          status: formData.status,
        });
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
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-header-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="1" y="3" width="15" height="13" />
              <polygon points="16 8 20 8 23 11 23 16 16 16 16 8" />
              <circle cx="5.5" cy="18.5" r="2.5" />
              <circle cx="18.5" cy="18.5" r="2.5" />
            </svg>
          </div>
          <div className="modal-header-text">
            <h2 className="modal-title">
              {isStatusOnly
                ? `Update Fleet Status • ${vehicle?.registration_number}`
                : isEdit
                ? `Edit Vehicle #${vehicle?.id}`
                : 'Register Fleet Vehicle'}
            </h2>
            <p className="modal-subtitle">
              {isStatusOnly
                ? 'Update operational maintenance or dispatch availability'
                : 'Add a new transport asset to the centralized fleet directory'}
            </p>
          </div>
          <button type="button" className="modal-close-btn" onClick={onClose} aria-label="Close modal">×</button>
        </div>

        {apiError && (
          <div className="auth-alert error" style={{ margin: '0 24px 16px' }} role="alert">
            <div className="auth-alert-content">
              <span className="auth-alert-title">Vehicle Action Failed</span>
              <span className="auth-alert-text">{apiError}</span>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="modal-form">
          {!isStatusOnly && (
            <>
              <div className="form-row-2">
                <div className="form-group">
                  <label className="form-label" htmlFor="veh-reg">Registration Plate *</label>
                  <input
                    id="veh-reg"
                    type="text"
                    className={`form-input ${errors.registration_number ? 'input-error' : ''}`}
                    placeholder="e.g. FL-TX-8821"
                    value={formData.registration_number}
                    onChange={(e) => setFormData({ ...formData, registration_number: e.target.value })}
                    disabled={isSubmitting}
                  />
                  {errors.registration_number && <span className="field-error-text">{errors.registration_number}</span>}
                </div>

                <div className="form-group">
                  <label className="form-label" htmlFor="veh-type">Vehicle Classification *</label>
                  <select
                    id="veh-type"
                    className={`form-input form-select ${errors.vehicle_type ? 'input-error' : ''}`}
                    value={formData.vehicle_type}
                    onChange={(e) => setFormData({ ...formData, vehicle_type: e.target.value })}
                    disabled={isSubmitting}
                  >
                    <option value="Semi-Trailer">Semi-Trailer (18-Wheeler)</option>
                    <option value="Box Truck">Box Truck (Medium Duty)</option>
                    <option value="Cargo Van">Cargo Van (Sprinter / Express)</option>
                    <option value="Flatbed">Flatbed Carrier</option>
                    <option value="Refrigerated Truck">Refrigerated Truck (Cold Chain)</option>
                  </select>
                  {errors.vehicle_type && <span className="field-error-text">{errors.vehicle_type}</span>}
                </div>
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="veh-cap">Max Payload Capacity (kg) *</label>
                <input
                  id="veh-cap"
                  type="number"
                  min="1"
                  step="50"
                  className={`form-input ${errors.capacity ? 'input-error' : ''}`}
                  placeholder="e.g. 18000"
                  value={formData.capacity}
                  onChange={(e) => setFormData({ ...formData, capacity: e.target.value })}
                  disabled={isSubmitting}
                />
                {errors.capacity && <span className="field-error-text">{errors.capacity}</span>}
              </div>
            </>
          )}

          <div className="form-group">
            <label className="form-label" htmlFor="veh-status">Operational Status *</label>
            <select
              id="veh-status"
              className={`form-input form-select ${errors.status ? 'input-error' : ''}`}
              value={formData.status}
              onChange={(e) => setFormData({ ...formData, status: e.target.value })}
              disabled={isSubmitting}
            >
              <option value="AVAILABLE">AVAILABLE (Depot Ready)</option>
              <option value="IN_USE">IN_USE (Currently Dispatched)</option>
              <option value="MAINTENANCE">MAINTENANCE (Workshop / Service)</option>
              <option value="DECOMMISSIONED">DECOMMISSIONED (Out of Service)</option>
            </select>
            {errors.status && <span className="field-error-text">{errors.status}</span>}
          </div>

          <div className="modal-actions">
            <button
              type="button"
              className="btn-action outline"
              onClick={onClose}
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn-action primary"
              disabled={isSubmitting}
            >
              {isSubmitting
                ? 'Saving...'
                : isStatusOnly
                ? 'Update Status'
                : isEdit
                ? 'Save Vehicle'
                : 'Register Asset'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
