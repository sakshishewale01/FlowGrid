import React, { useState, useEffect } from 'react';
import { warehousesApi } from '../api/warehouses.js';
import { formatErrorMessage } from '../api/client.js';

/**
 * WarehouseModal component for creating and editing warehouse facilities.
 *
 * @param {Object} props
 * @param {boolean} props.isOpen
 * @param {Function} props.onClose
 * @param {Object|null} props.warehouse - If present, edit mode; otherwise create mode
 * @param {Function} props.onSaved - Callback with saved warehouse record
 */
export default function WarehouseModal({ isOpen, onClose, warehouse = null, onSaved }) {
  const isEdit = Boolean(warehouse);

  const [formData, setFormData] = useState({
    name: '',
    location: '',
    address: '',
    capacity: 25000,
    is_active: true,
  });
  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [apiError, setApiError] = useState(null);

  useEffect(() => {
    if (warehouse) {
      setFormData({
        name: warehouse.name || '',
        location: warehouse.location || '',
        address: warehouse.address || '',
        capacity: warehouse.capacity || 25000,
        is_active: warehouse.is_active ?? true,
      });
    } else {
      setFormData({
        name: '',
        location: '',
        address: '',
        capacity: 25000,
        is_active: true,
      });
    }
    setErrors({});
    setApiError(null);
  }, [warehouse, isOpen]);

  if (!isOpen) return null;

  const validate = () => {
    const errs = {};
    const trimmedName = formData.name.trim();
    if (!trimmedName) {
      errs.name = 'Facility name is required.';
    } else if (trimmedName.length < 2) {
      errs.name = 'Facility name must be at least 2 characters.';
    } else if (trimmedName.length > 100) {
      errs.name = 'Facility name must not exceed 100 characters.';
    }

    const trimmedLocation = formData.location.trim();
    if (!trimmedLocation) {
      errs.location = 'City / Region is required.';
    } else if (trimmedLocation.length < 2) {
      errs.location = 'City / Region must be at least 2 characters.';
    } else if (trimmedLocation.length > 150) {
      errs.location = 'City / Region must not exceed 150 characters.';
    }

    const trimmedAddress = formData.address.trim();
    if (!trimmedAddress) {
      errs.address = 'Street address is required.';
    } else if (trimmedAddress.length < 3) {
      errs.address = 'Street address must be at least 3 characters.';
    } else if (trimmedAddress.length > 255) {
      errs.address = 'Street address must not exceed 255 characters.';
    }

    const capNum = Number(formData.capacity);
    if (!formData.capacity || isNaN(capNum) || capNum <= 0) {
      errs.capacity = 'Storage capacity must be greater than 0.';
    } else if (capNum > 50000000) {
      errs.capacity = 'Capacity cannot exceed 50,000,000 units.';
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
        location: formData.location.trim(),
        address: formData.address.trim(),
        capacity: Number(formData.capacity),
        is_active: Boolean(formData.is_active),
      };

      let result;
      if (isEdit) {
        result = await warehousesApi.updateWarehouse(warehouse.id, payload);
      } else {
        result = await warehousesApi.createWarehouse(payload);
      }

      if (onSaved) {
        onSaved(result, isEdit);
      }
      onClose();
    } catch (err) {
      setApiError(formatErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="modal-backdrop" onClick={onClose} role="dialog" aria-modal="true" aria-labelledby="wh-modal-title">
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-header-icon" aria-hidden="true">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 21h18M3 7v14m18-14v14M6 11h4m-4 4h4m4-4h4m-4 4h4M9 3h6l3 4H6l3-4z" />
            </svg>
          </div>
          <div className="modal-header-text">
            <h2 id="wh-modal-title" className="modal-title">
              {isEdit ? `Edit Warehouse #${warehouse.id}` : 'Register a Warehouse'}
            </h2>
            <p className="modal-subtitle">
              {isEdit
                ? 'Modify location details, floor capacity, or operational status.'
                : 'Add a facility to your logistics network.'}
            </p>
          </div>
          <button type="button" className="modal-close-btn" onClick={onClose} aria-label="Close modal">×</button>
        </div>

        {apiError && (
          <div className="auth-alert error" style={{ margin: '16px 24px 0' }} role="alert">
            <div className="auth-alert-content">
              <span className="auth-alert-title">Operation Failed</span>
              <span className="auth-alert-text">{apiError}</span>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="modal-form" noValidate>
          {/* Facility Name */}
          <div className="form-group">
            <label className="form-label" htmlFor="wh-name">
              <span className="form-label-title">
                Facility Name <span className="form-required-star" aria-hidden="true">*</span>
              </span>
            </label>
            <input
              id="wh-name"
              type="text"
              className={`form-input ${errors.name ? 'input-error' : ''}`}
              placeholder="e.g. Pune Central Logistics Hub"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              disabled={isSubmitting}
              aria-required="true"
              aria-invalid={Boolean(errors.name)}
              aria-describedby={errors.name ? 'wh-name-error' : undefined}
            />
            {errors.name && (
              <span id="wh-name-error" className="field-error-text" role="alert">
                {errors.name}
              </span>
            )}
          </div>

          {/* City / Region & Storage Capacity */}
          <div className="form-row-2">
            <div className="form-group">
              <label className="form-label" htmlFor="wh-location">
                <span className="form-label-title">
                  City / Region <span className="form-required-star" aria-hidden="true">*</span>
                </span>
              </label>
              <input
                id="wh-location"
                type="text"
                list="wh-supported-regions"
                className={`form-input ${errors.location ? 'input-error' : ''}`}
                placeholder="e.g. Pune, Maharashtra"
                value={formData.location}
                onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                disabled={isSubmitting}
                aria-required="true"
                aria-invalid={Boolean(errors.location)}
                aria-describedby={errors.location ? 'wh-location-error' : 'wh-location-hint'}
              />
              <datalist id="wh-supported-regions">
                <option value="Pune, Maharashtra" />
                <option value="Delhi NCR" />
                <option value="Chennai, Tamil Nadu" />
                <option value="Ahmedabad, Gujarat" />
                <option value="Kolkata, West Bengal" />
                <option value="Mumbai, Maharashtra" />
                <option value="Bengaluru, Karnataka" />
                <option value="Hyderabad, Telangana" />
              </datalist>
              <span id="wh-location-hint" className="form-hint">Metropolitan logistics zone or hub city</span>
              {errors.location && (
                <span id="wh-location-error" className="field-error-text" role="alert">
                  {errors.location}
                </span>
              )}
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="wh-capacity">
                <span className="form-label-title">
                  Storage Capacity <span className="form-required-star" aria-hidden="true">*</span>
                </span>
              </label>
              <div className="input-with-unit-wrapper">
                <input
                  id="wh-capacity"
                  type="number"
                  min="1"
                  max="50000000"
                  step="1"
                  className={`form-input ${errors.capacity ? 'input-error' : ''}`}
                  placeholder="e.g. 50000"
                  value={formData.capacity}
                  onChange={(e) => setFormData({ ...formData, capacity: e.target.value })}
                  disabled={isSubmitting}
                  aria-required="true"
                  aria-invalid={Boolean(errors.capacity)}
                  aria-describedby={errors.capacity ? 'wh-capacity-error' : 'wh-capacity-hint'}
                />
                <span className="input-unit-badge">Units / Pallets</span>
              </div>
              <span id="wh-capacity-hint" className="form-hint">Total available floor storage positions</span>
              {errors.capacity && (
                <span id="wh-capacity-error" className="field-error-text" role="alert">
                  {errors.capacity}
                </span>
              )}
            </div>
          </div>

          {/* Street Address */}
          <div className="form-group">
            <label className="form-label" htmlFor="wh-address">
              <span className="form-label-title">
                Street Address <span className="form-required-star" aria-hidden="true">*</span>
              </span>
            </label>
            <input
              id="wh-address"
              type="text"
              className={`form-input ${errors.address ? 'input-error' : ''}`}
              placeholder="e.g. Plot 42, Hinjewadi Phase 2, MIDC, Pune 411057"
              value={formData.address}
              onChange={(e) => setFormData({ ...formData, address: e.target.value })}
              disabled={isSubmitting}
              aria-required="true"
              aria-invalid={Boolean(errors.address)}
              aria-describedby={errors.address ? 'wh-address-error' : 'wh-address-hint'}
            />
            <span id="wh-address-hint" className="form-hint">Full road, dock, or parcel identifier</span>
            {errors.address && (
              <span id="wh-address-error" className="field-error-text" role="alert">
                {errors.address}
              </span>
            )}
          </div>

          {/* Active Status */}
          <div className="form-group">
            <label
              className={`form-checkbox-card ${formData.is_active ? 'checked' : ''}`}
              htmlFor="wh-active"
            >
              <input
                id="wh-active"
                type="checkbox"
                checked={formData.is_active}
                onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                disabled={isSubmitting}
              />
              <div className="form-checkbox-content">
                <span className="form-checkbox-title">This facility can receive and dispatch freight.</span>
                <span className="form-checkbox-desc">
                  When enabled, this facility is operational and eligible for shipment allocation, inventory intake, and route assignments.
                </span>
              </div>
            </label>
          </div>

          {/* Actions */}
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
              style={{ minWidth: '170px' }}
            >
              {isSubmitting ? (
                <>
                  <span className="spinner-inline" aria-hidden="true" />
                  <span>Saving Facility...</span>
                </>
              ) : isEdit ? (
                'Update Warehouse'
              ) : (
                'Register Warehouse'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
