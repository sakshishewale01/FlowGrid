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
    if (!formData.name.trim() || formData.name.trim().length < 2) {
      errs.name = 'Warehouse name must be at least 2 characters.';
    }
    if (!formData.location.trim() || formData.location.trim().length < 2) {
      errs.location = 'Location (e.g. city/state) must be at least 2 characters.';
    }
    if (!formData.address.trim() || formData.address.trim().length < 3) {
      errs.address = 'Street address must be at least 3 characters.';
    }
    if (!formData.capacity || Number(formData.capacity) <= 0) {
      errs.capacity = 'Capacity must be greater than 0.';
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
          <div className="modal-header-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M3 21h18M3 7v14m18-14v14M6 11h4m-4 4h4m4-4h4m-4 4h4M9 3h6l3 4H6l3-4z" />
            </svg>
          </div>
          <div className="modal-header-text">
            <h2 id="wh-modal-title" className="modal-title">
              {isEdit ? `Edit Warehouse #${warehouse.id}` : 'Register Warehouse Facility'}
            </h2>
            <p className="modal-subtitle">
              {isEdit ? 'Modify location details, floor capacity, or operational status' : 'Add a new distribution terminal or fulfillment center to FlowGrid'}
            </p>
          </div>
          <button type="button" className="modal-close-btn" onClick={onClose} aria-label="Close modal">×</button>
        </div>

        {apiError && (
          <div className="auth-alert error" style={{ margin: '0 24px 16px' }} role="alert">
            <div className="auth-alert-content">
              <span className="auth-alert-title">Operation Failed</span>
              <span className="auth-alert-text">{apiError}</span>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="modal-form">
          <div className="form-group">
            <label className="form-label" htmlFor="wh-name">Facility Name *</label>
            <input
              id="wh-name"
              type="text"
              className={`form-input ${errors.name ? 'input-error' : ''}`}
              placeholder="e.g. Chicago Central Hub"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              disabled={isSubmitting}
            />
            {errors.name && <span className="field-error-text">{errors.name}</span>}
          </div>

          <div className="form-row-2">
            <div className="form-group">
              <label className="form-label" htmlFor="wh-location">Metropolitan Region *</label>
              <input
                id="wh-location"
                type="text"
                className={`form-input ${errors.location ? 'input-error' : ''}`}
                placeholder="e.g. Chicago, IL"
                value={formData.location}
                onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                disabled={isSubmitting}
              />
              {errors.location && <span className="field-error-text">{errors.location}</span>}
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="wh-capacity">Pallet / Unit Capacity *</label>
              <input
                id="wh-capacity"
                type="number"
                min="1"
                step="1"
                className={`form-input ${errors.capacity ? 'input-error' : ''}`}
                placeholder="e.g. 50000"
                value={formData.capacity}
                onChange={(e) => setFormData({ ...formData, capacity: e.target.value })}
                disabled={isSubmitting}
              />
              {errors.capacity && <span className="field-error-text">{errors.capacity}</span>}
            </div>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="wh-address">Street Address *</label>
            <input
              id="wh-address"
              type="text"
              className={`form-input ${errors.address ? 'input-error' : ''}`}
              placeholder="e.g. 1200 Logistics Blvd, Dock 4, Chicago, IL 60601"
              value={formData.address}
              onChange={(e) => setFormData({ ...formData, address: e.target.value })}
              disabled={isSubmitting}
            />
            {errors.address && <span className="field-error-text">{errors.address}</span>}
          </div>

          <div className="form-group checkbox-group">
            <label className="checkbox-label" htmlFor="wh-active">
              <input
                id="wh-active"
                type="checkbox"
                checked={formData.is_active}
                onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                disabled={isSubmitting}
              />
              <span>Facility is actively receiving and dispatching freight</span>
            </label>
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
              {isSubmitting ? 'Saving...' : isEdit ? 'Update Warehouse' : 'Register Warehouse'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
