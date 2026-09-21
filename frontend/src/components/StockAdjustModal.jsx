import React, { useState, useEffect } from 'react';
import { inventoryApi } from '../api/inventory.js';
import { formatErrorMessage } from '../api/client.js';

/**
 * StockAdjustModal for stock adjustments, warehouse transfers, and new inventory links.
 *
 * @param {Object} props
 * @param {boolean} props.isOpen
 * @param {Function} props.onClose
 * @param {'adjust'|'transfer'|'create'} props.mode
 * @param {Object|null} props.item - Target inventory record (for adjust or transfer)
 * @param {Array} props.warehouses - List of all warehouses
 * @param {Array} props.products - List of catalog products
 * @param {Function} props.onSuccess - Callback after successful mutation
 */
export default function StockAdjustModal({
  isOpen,
  onClose,
  mode = 'adjust',
  item = null,
  warehouses = [],
  products = [],
  onSuccess,
}) {
  const [formData, setFormData] = useState({
    quantity: 0,
    reorder_level: 10,
    target_warehouse_id: '',
    transfer_quantity: 1,
    selected_warehouse_id: '',
    selected_product_id: '',
  });

  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [apiError, setApiError] = useState(null);

  useEffect(() => {
    if (item) {
      setFormData({
        quantity: item.quantity ?? 0,
        reorder_level: item.reorder_level ?? 10,
        target_warehouse_id: '',
        transfer_quantity: 1,
        selected_warehouse_id: item.warehouse_id || '',
        selected_product_id: item.product_id || '',
      });
    } else {
      setFormData({
        quantity: 50,
        reorder_level: 15,
        target_warehouse_id: '',
        transfer_quantity: 1,
        selected_warehouse_id: warehouses[0]?.id || '',
        selected_product_id: products[0]?.id || '',
      });
    }
    setErrors({});
    setApiError(null);
  }, [item, mode, isOpen, warehouses, products]);

  if (!isOpen) return null;

  const validate = () => {
    const errs = {};
    if (mode === 'adjust') {
      if (formData.quantity === '' || Number(formData.quantity) < 0) {
        errs.quantity = 'Quantity must be greater than or equal to 0.';
      }
      if (formData.reorder_level === '' || Number(formData.reorder_level) < 0) {
        errs.reorder_level = 'Reorder level must be greater than or equal to 0.';
      }
    } else if (mode === 'transfer') {
      if (!formData.target_warehouse_id) {
        errs.target_warehouse_id = 'Please select a destination warehouse.';
      } else if (Number(formData.target_warehouse_id) === Number(item?.warehouse_id)) {
        errs.target_warehouse_id = 'Destination must be different from source warehouse.';
      }
      const qty = Number(formData.transfer_quantity);
      if (!qty || qty <= 0) {
        errs.transfer_quantity = 'Transfer amount must be at least 1.';
      } else if (item && qty > item.quantity) {
        errs.transfer_quantity = `Cannot transfer more than on-hand stock (${item.quantity}).`;
      }
    } else if (mode === 'create') {
      if (!formData.selected_warehouse_id) {
        errs.selected_warehouse_id = 'Select a warehouse.';
      }
      if (!formData.selected_product_id) {
        errs.selected_product_id = 'Select a product.';
      }
      if (formData.quantity === '' || Number(formData.quantity) < 0) {
        errs.quantity = 'Initial quantity must be >= 0.';
      }
      if (formData.reorder_level === '' || Number(formData.reorder_level) < 0) {
        errs.reorder_level = 'Reorder level must be >= 0.';
      }
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
      if (mode === 'adjust' && item) {
        await inventoryApi.updateInventory(item.id, {
          quantity: Number(formData.quantity),
          reorder_level: Number(formData.reorder_level),
        });
      } else if (mode === 'transfer' && item) {
        const transferQty = Number(formData.transfer_quantity);
        const targetWhId = Number(formData.target_warehouse_id);

        // 1. Find existing inventory record at destination for this product
        const destRecords = await inventoryApi.listInventory({
          warehouse_id: targetWhId,
          product_id: item.product_id,
        });

        // 2. Adjust or create at destination
        if (destRecords && destRecords.length > 0) {
          const destRec = destRecords[0];
          await inventoryApi.updateInventory(destRec.id, {
            quantity: destRec.quantity + transferQty,
          });
        } else {
          await inventoryApi.createInventory({
            warehouse_id: targetWhId,
            product_id: item.product_id,
            quantity: transferQty,
            reorder_level: item.reorder_level || 10,
          });
        }

        // 3. Deduct from source
        await inventoryApi.updateInventory(item.id, {
          quantity: item.quantity - transferQty,
        });
      } else if (mode === 'create') {
        await inventoryApi.createInventory({
          warehouse_id: Number(formData.selected_warehouse_id),
          product_id: Number(formData.selected_product_id),
          quantity: Number(formData.quantity),
          reorder_level: Number(formData.reorder_level),
        });
      }

      if (onSuccess) onSuccess();
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
              <path d="M4 6h16M4 10h16M4 14h16M4 18h16" />
            </svg>
          </div>
          <div className="modal-header-text">
            <h2 className="modal-title">
              {mode === 'adjust' && `Adjust Stock • ${item?.product?.name || 'Item'}`}
              {mode === 'transfer' && `Transfer Stock • ${item?.product?.name || 'Item'}`}
              {mode === 'create' && 'New Inventory Allocation'}
            </h2>
            <p className="modal-subtitle">
              {mode === 'adjust' && `Current Location: ${item?.warehouse?.name || 'Warehouse'}`}
              {mode === 'transfer' && `Transfer units between distribution hubs`}
              {mode === 'create' && `Assign a catalog product to a warehouse`}
            </p>
          </div>
          <button type="button" className="modal-close-btn" onClick={onClose} aria-label="Close modal">×</button>
        </div>

        {apiError && (
          <div className="auth-alert error" style={{ margin: '0 24px 16px' }} role="alert">
            <div className="auth-alert-content">
              <span className="auth-alert-title">Action Failed</span>
              <span className="auth-alert-text">{apiError}</span>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="modal-form">
          {mode === 'adjust' && (
            <>
              <div className="form-row-2">
                <div className="form-group">
                  <label className="form-label" htmlFor="inv-qty">On-Hand Quantity *</label>
                  <input
                    id="inv-qty"
                    type="number"
                    min="0"
                    step="1"
                    className={`form-input ${errors.quantity ? 'input-error' : ''}`}
                    value={formData.quantity}
                    onChange={(e) => setFormData({ ...formData, quantity: e.target.value })}
                    disabled={isSubmitting}
                  />
                  {errors.quantity && <span className="field-error-text">{errors.quantity}</span>}
                </div>

                <div className="form-group">
                  <label className="form-label" htmlFor="inv-reorder">Reorder Threshold *</label>
                  <input
                    id="inv-reorder"
                    type="number"
                    min="0"
                    step="1"
                    className={`form-input ${errors.reorder_level ? 'input-error' : ''}`}
                    value={formData.reorder_level}
                    onChange={(e) => setFormData({ ...formData, reorder_level: e.target.value })}
                    disabled={isSubmitting}
                  />
                  {errors.reorder_level && <span className="field-error-text">{errors.reorder_level}</span>}
                </div>
              </div>
              <p className="form-hint" style={{ fontSize: '0.78rem', color: '#94A3B8' }}>
                Adjusting on-hand quantity immediately updates available inventory counts across all fulfillment routes.
              </p>
            </>
          )}

          {mode === 'transfer' && (
            <>
              <div className="form-group">
                <label className="form-label">Source Warehouse</label>
                <input
                  type="text"
                  className="form-input"
                  value={`${item?.warehouse?.name || 'Warehouse'} (${item?.quantity || 0} units on hand)`}
                  disabled
                />
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="inv-target-wh">Destination Warehouse *</label>
                <select
                  id="inv-target-wh"
                  className={`form-input form-select ${errors.target_warehouse_id ? 'input-error' : ''}`}
                  value={formData.target_warehouse_id}
                  onChange={(e) => setFormData({ ...formData, target_warehouse_id: e.target.value })}
                  disabled={isSubmitting}
                >
                  <option value="">-- Select Destination Facility --</option>
                  {warehouses
                    .filter((w) => w.id !== item?.warehouse_id && w.is_active)
                    .map((w) => (
                      <option key={w.id} value={w.id}>
                        {w.name} ({w.location})
                      </option>
                    ))}
                </select>
                {errors.target_warehouse_id && <span className="field-error-text">{errors.target_warehouse_id}</span>}
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="inv-transfer-qty">Quantity to Transfer *</label>
                <input
                  id="inv-transfer-qty"
                  type="number"
                  min="1"
                  max={item?.quantity || 9999}
                  step="1"
                  className={`form-input ${errors.transfer_quantity ? 'input-error' : ''}`}
                  value={formData.transfer_quantity}
                  onChange={(e) => setFormData({ ...formData, transfer_quantity: e.target.value })}
                  disabled={isSubmitting}
                />
                {errors.transfer_quantity && <span className="field-error-text">{errors.transfer_quantity}</span>}
              </div>
            </>
          )}

          {mode === 'create' && (
            <>
              <div className="form-group">
                <label className="form-label" htmlFor="inv-new-wh">Warehouse Facility *</label>
                <select
                  id="inv-new-wh"
                  className={`form-input form-select ${errors.selected_warehouse_id ? 'input-error' : ''}`}
                  value={formData.selected_warehouse_id}
                  onChange={(e) => setFormData({ ...formData, selected_warehouse_id: e.target.value })}
                  disabled={isSubmitting}
                >
                  <option value="">-- Select Warehouse --</option>
                  {warehouses.map((w) => (
                    <option key={w.id} value={w.id}>
                      {w.name} ({w.location})
                    </option>
                  ))}
                </select>
                {errors.selected_warehouse_id && <span className="field-error-text">{errors.selected_warehouse_id}</span>}
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="inv-new-prod">Catalog Product *</label>
                <select
                  id="inv-new-prod"
                  className={`form-input form-select ${errors.selected_product_id ? 'input-error' : ''}`}
                  value={formData.selected_product_id}
                  onChange={(e) => setFormData({ ...formData, selected_product_id: e.target.value })}
                  disabled={isSubmitting}
                >
                  <option value="">-- Select Product --</option>
                  {products.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name} (SKU: {p.sku})
                    </option>
                  ))}
                </select>
                {errors.selected_product_id && <span className="field-error-text">{errors.selected_product_id}</span>}
              </div>

              <div className="form-row-2">
                <div className="form-group">
                  <label className="form-label" htmlFor="inv-new-qty">Initial Stock *</label>
                  <input
                    id="inv-new-qty"
                    type="number"
                    min="0"
                    step="1"
                    className={`form-input ${errors.quantity ? 'input-error' : ''}`}
                    value={formData.quantity}
                    onChange={(e) => setFormData({ ...formData, quantity: e.target.value })}
                    disabled={isSubmitting}
                  />
                  {errors.quantity && <span className="field-error-text">{errors.quantity}</span>}
                </div>

                <div className="form-group">
                  <label className="form-label" htmlFor="inv-new-reorder">Reorder Threshold *</label>
                  <input
                    id="inv-new-reorder"
                    type="number"
                    min="0"
                    step="1"
                    className={`form-input ${errors.reorder_level ? 'input-error' : ''}`}
                    value={formData.reorder_level}
                    onChange={(e) => setFormData({ ...formData, reorder_level: e.target.value })}
                    disabled={isSubmitting}
                  />
                  {errors.reorder_level && <span className="field-error-text">{errors.reorder_level}</span>}
                </div>
              </div>
            </>
          )}

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
                ? 'Processing...'
                : mode === 'adjust'
                ? 'Save Adjustment'
                : mode === 'transfer'
                ? 'Execute Transfer'
                : 'Link Inventory'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
