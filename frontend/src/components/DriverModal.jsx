import React, { useState, useEffect } from 'react';
import { driversApi } from '../api/drivers.js';
import { formatErrorMessage } from '../api/client.js';

/**
 * DriverModal for registering new drivers or updating driver operational status.
 *
 * @param {Object} props
 * @param {boolean} props.isOpen
 * @param {Function} props.onClose
 * @param {Object|null} props.driver - Driver record if editing/updating
 * @param {boolean} props.isStatusOnly - If true, only allow updating availability status
 * @param {Function} props.onSaved - Callback after driver saved
 */
export default function DriverModal({
  isOpen,
  onClose,
  driver = null,
  isStatusOnly = false,
  onSaved,
}) {
  const isEdit = Boolean(driver);

  const [formData, setFormData] = useState({
    user_id: 1,
    license_number: '',
    phone_number: '',
    availability_status: 'AVAILABLE',
  });

  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [apiError, setApiError] = useState(null);

  useEffect(() => {
    if (driver) {
      setFormData({
        user_id: driver.user_id || 1,
        license_number: driver.license_number || '',
        phone_number: driver.phone_number || '',
        availability_status: driver.availability_status || 'AVAILABLE',
      });
    } else {
      setFormData({
        user_id: 1,
        license_number: '',
        phone_number: '',
        availability_status: 'AVAILABLE',
      });
    }
    setErrors({});
    setApiError(null);
  }, [driver, isOpen]);

  if (!isOpen) return null;

  const validate = () => {
    const errs = {};
    if (!isStatusOnly) {
      if (!isEdit && (!formData.user_id || Number(formData.user_id) <= 0)) {
        errs.user_id = 'Valid user ID is required.';
      }
      if (!formData.license_number.trim() || formData.license_number.trim().length < 3) {
        errs.license_number = 'License number must be at least 3 characters.';
      }
      if (!formData.phone_number.trim() || formData.phone_number.trim().length < 7) {
        errs.phone_number = 'Phone number must be at least 7 characters.';
      }
    }
    if (!formData.availability_status) {
      errs.availability_status = 'Status is required.';
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
      if (isStatusOnly && driver) {
        result = await driversApi.updateDriver(driver.id, {
          availability_status: formData.availability_status,
        });
      } else if (isEdit) {
        result = await driversApi.updateDriver(driver.id, {
          license_number: formData.license_number.trim(),
          phone_number: formData.phone_number.trim(),
          availability_status: formData.availability_status,
        });
      } else {
        result = await driversApi.createDriver({
          user_id: Number(formData.user_id),
          license_number: formData.license_number.trim(),
          phone_number: formData.phone_number.trim(),
          availability_status: formData.availability_status,
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
              <path d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
          </div>
          <div className="modal-header-text">
            <h2 className="modal-title">
              {isStatusOnly
                ? `Update Dispatch Status • Driver #${driver?.id}`
                : isEdit
                ? `Edit Driver Profile #${driver?.id}`
                : 'Register New Fleet Driver'}
            </h2>
            <p className="modal-subtitle">
              {isStatusOnly
                ? 'Update field operational availability for route dispatching'
                : 'Link mobile logistics personnel to FlowGrid dispatch network'}
            </p>
          </div>
          <button type="button" className="modal-close-btn" onClick={onClose} aria-label="Close modal">×</button>
        </div>

        {apiError && (
          <div className="auth-alert error" style={{ margin: '0 24px 16px' }} role="alert">
            <div className="auth-alert-content">
              <span className="auth-alert-title">Driver Action Failed</span>
              <span className="auth-alert-text">{apiError}</span>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="modal-form">
          {!isStatusOnly && !isEdit && (
            <div className="form-group">
              <label className="form-label" htmlFor="driver-user-id">Linked User ID *</label>
              <input
                id="driver-user-id"
                type="number"
                min="1"
                step="1"
                className={`form-input ${errors.user_id ? 'input-error' : ''}`}
                placeholder="User account primary key (e.g. 1)"
                value={formData.user_id}
                onChange={(e) => setFormData({ ...formData, user_id: e.target.value })}
                disabled={isSubmitting}
              />
              {errors.user_id && <span className="field-error-text">{errors.user_id}</span>}
              <span className="form-hint" style={{ fontSize: '0.76rem', color: '#94A3B8' }}>
                Driver profiles must link to an existing user account with DRIVER role.
              </span>
            </div>
          )}

          {!isStatusOnly && (
            <div className="form-row-2">
              <div className="form-group">
                <label className="form-label" htmlFor="driver-license">Driver License # *</label>
                <input
                  id="driver-license"
                  type="text"
                  className={`form-input ${errors.license_number ? 'input-error' : ''}`}
                  placeholder="e.g. DL-948201-TX"
                  value={formData.license_number}
                  onChange={(e) => setFormData({ ...formData, license_number: e.target.value })}
                  disabled={isSubmitting}
                />
                {errors.license_number && <span className="field-error-text">{errors.license_number}</span>}
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="driver-phone">Mobile Phone *</label>
                <input
                  id="driver-phone"
                  type="tel"
                  className={`form-input ${errors.phone_number ? 'input-error' : ''}`}
                  placeholder="e.g. +1-555-234-5678"
                  value={formData.phone_number}
                  onChange={(e) => setFormData({ ...formData, phone_number: e.target.value })}
                  disabled={isSubmitting}
                />
                {errors.phone_number && <span className="field-error-text">{errors.phone_number}</span>}
              </div>
            </div>
          )}

          <div className="form-group">
            <label className="form-label" htmlFor="driver-status">Operational Status *</label>
            <select
              id="driver-status"
              className={`form-input form-select ${errors.availability_status ? 'input-error' : ''}`}
              value={formData.availability_status}
              onChange={(e) => setFormData({ ...formData, availability_status: e.target.value })}
              disabled={isSubmitting}
            >
              <option value="AVAILABLE">AVAILABLE (Ready for Assignment)</option>
              <option value="ON_DUTY">ON_DUTY (Active Shift)</option>
              <option value="IN_TRANSIT">IN_TRANSIT (Driving / In Corridor)</option>
              <option value="OFF_DUTY">OFF_DUTY (Unavailable)</option>
            </select>
            {errors.availability_status && <span className="field-error-text">{errors.availability_status}</span>}
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
                ? 'Save Profile'
                : 'Register Driver'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
