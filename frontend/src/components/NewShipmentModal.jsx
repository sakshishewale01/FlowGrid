import React, { useState, useEffect } from 'react';
import { shipmentsApi, warehousesApi } from '../api/index.js';
import { useAuth } from '../context/useAuth.js';

export default function NewShipmentModal({ isOpen, onClose, onCreated }) {
  const { hasRole } = useAuth();
  const canCreate = hasRole(['ADMIN', 'MANAGER']);

  const [warehouses, setWarehouses] = useState([]);
  const [originWarehouseId, setOriginWarehouseId] = useState('');
  const [destinationAddress, setDestinationAddress] = useState('');
  const [destinationCity, setDestinationCity] = useState('');
  const [destinationState, setDestinationState] = useState('');
  const [destinationPostalCode, setDestinationPostalCode] = useState('');
  const [weightKg, setWeightKg] = useState('1250');
  const [volumeCbm, setVolumeCbm] = useState('6.5');

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  // Fetch active warehouses to populate origin dropdown
  useEffect(() => {
    if (isOpen) {
      warehousesApi
        .listWarehouses({ is_active: true })
        .then((data) => {
          if (Array.isArray(data)) {
            setWarehouses(data);
            if (data.length > 0 && !originWarehouseId) {
              setOriginWarehouseId(String(data[0].id));
            }
          }
        })
        .catch((err) => {
          console.warn('Failed to load warehouses for shipment modal:', err.message);
        });
    }
  }, [isOpen, originWarehouseId]);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!canCreate) {
      setErrorMessage('Action Denied: Creating shipments requires MANAGER or ADMIN role.');
      return;
    }

    if (!destinationAddress.trim() || !destinationCity.trim() || !destinationState.trim() || !destinationPostalCode.trim()) {
      setErrorMessage('Please complete all destination address fields.');
      return;
    }

    setIsSubmitting(true);
    setErrorMessage('');

    try {
      const payload = {
        origin_warehouse_id: originWarehouseId ? Number(originWarehouseId) : null,
        destination_address: destinationAddress.trim(),
        destination_city: destinationCity.trim(),
        destination_state: destinationState.trim(),
        destination_postal_code: destinationPostalCode.trim(),
        total_weight_kg: weightKg ? parseFloat(weightKg) : 0,
        total_volume_cbm: volumeCbm ? parseFloat(volumeCbm) : 0,
      };

      const created = await shipmentsApi.createShipment(payload);
      if (onCreated) {
        onCreated(created);
      }
      onClose();
    } catch (err) {
      setErrorMessage(err.message || 'Failed to create shipment order.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose} id="modal-new-shipment-overlay">
      <div className="waybill-modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '540px' }}>
        <div className="modal-header">
          <div className="modal-title-group">
            <span className="modal-tag">LOGISTICS OPERATIONS DISPATCH</span>
            <h3 className="modal-title">Create New Line-Haul Shipment</h3>
          </div>
          <button className="modal-close-btn" onClick={onClose} aria-label="Close modal">
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="waybill-body">
            {errorMessage && (
              <div className="auth-alert error" role="alert" style={{ marginBottom: '14px' }}>
                <span className="auth-alert-text">{errorMessage}</span>
              </div>
            )}

            <div className="auth-field" style={{ marginBottom: '12px' }}>
              <label className="auth-label">Origin Warehouse Facility</label>
              <select
                className="auth-input"
                style={{ paddingLeft: '12px' }}
                value={originWarehouseId}
                onChange={(e) => setOriginWarehouseId(e.target.value)}
                required
              >
                {warehouses.map((wh) => (
                  <option key={wh.id} value={wh.id}>
                    {wh.name} — {wh.location}
                  </option>
                ))}
              </select>
            </div>

            <div className="auth-field" style={{ marginBottom: '12px' }}>
              <label className="auth-label">Destination Street Address</label>
              <input
                type="text"
                className="auth-input"
                style={{ paddingLeft: '12px' }}
                placeholder="e.g. 500 Freight Depot Way"
                value={destinationAddress}
                onChange={(e) => setDestinationAddress(e.target.value)}
                required
              />
            </div>

            <div className="auth-grid-2col" style={{ marginBottom: '12px' }}>
              <div className="auth-field">
                <label className="auth-label">City</label>
                <input
                  type="text"
                  className="auth-input"
                  style={{ paddingLeft: '12px' }}
                  placeholder="e.g. Milwaukee"
                  value={destinationCity}
                  onChange={(e) => setDestinationCity(e.target.value)}
                  required
                />
              </div>

              <div className="auth-field">
                <label className="auth-label">State &amp; ZIP</label>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                  <input
                    type="text"
                    className="auth-input"
                    style={{ paddingLeft: '12px' }}
                    placeholder="WI"
                    maxLength={2}
                    value={destinationState}
                    onChange={(e) => setDestinationState(e.target.value.toUpperCase())}
                    required
                  />
                  <input
                    type="text"
                    className="auth-input"
                    style={{ paddingLeft: '12px' }}
                    placeholder="53202"
                    value={destinationPostalCode}
                    onChange={(e) => setDestinationPostalCode(e.target.value)}
                    required
                  />
                </div>
              </div>
            </div>

            <div className="auth-grid-2col">
              <div className="auth-field">
                <label className="auth-label">Weight (kg)</label>
                <input
                  type="number"
                  step="0.01"
                  className="auth-input"
                  style={{ paddingLeft: '12px' }}
                  value={weightKg}
                  onChange={(e) => setWeightKg(e.target.value)}
                  required
                />
              </div>

              <div className="auth-field">
                <label className="auth-label">Volume (CBM)</label>
                <input
                  type="number"
                  step="0.01"
                  className="auth-input"
                  style={{ paddingLeft: '12px' }}
                  value={volumeCbm}
                  onChange={(e) => setVolumeCbm(e.target.value)}
                  required
                />
              </div>
            </div>
          </div>

          <div className="modal-footer" style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
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
              className="auth-btn-primary"
              disabled={isSubmitting}
              id="btn-confirm-create-shipment"
              style={{ minWidth: '160px', marginTop: 0 }}
            >
              {isSubmitting ? 'Creating Order...' : 'Dispatch Shipment'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
