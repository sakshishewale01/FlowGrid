import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useAuth } from '../context/AuthContext';
import { inventoryApi } from '../api/inventory.js';
import { warehousesApi } from '../api/warehouses.js';
import { productsApi } from '../api/products.js';
import { formatErrorMessage } from '../api/client.js';
import PageHeader from '../components/PageHeader';
import StockAdjustModal from '../components/StockAdjustModal';

export default function InventoryPage() {
  const { user } = useAuth();
  const isManagerOrAdmin = user?.role === 'ADMIN' || user?.role === 'MANAGER';

  const [inventory, setInventory] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters
  const [selectedWarehouseId, setSelectedWarehouseId] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL'); // 'ALL' | 'HEALTHY' | 'LOW_STOCK' | 'OUT_OF_STOCK'

  // Modal control
  const [modalState, setModalState] = useState({
    isOpen: false,
    mode: 'adjust', // 'adjust' | 'transfer' | 'create'
    item: null,
  });

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [invRes, whRes, prodRes] = await Promise.allSettled([
        inventoryApi.listInventory({ limit: 250 }),
        warehousesApi.listWarehouses({ limit: 100 }),
        productsApi.listProducts({ limit: 100 }),
      ]);

      if (invRes.status === 'fulfilled') setInventory(invRes.value || []);
      if (whRes.status === 'fulfilled') setWarehouses(whRes.value || []);
      if (prodRes.status === 'fulfilled') setProducts(prodRes.value || []);
    } catch (err) {
      setError(formatErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const getStockStatus = (item) => {
    if (item.quantity === 0) return 'OUT_OF_STOCK';
    if (item.quantity <= (item.reorder_level || 10)) return 'LOW_STOCK';
    return 'HEALTHY';
  };

  const filteredInventory = useMemo(() => {
    return inventory.filter((item) => {
      // Filter by Warehouse
      if (selectedWarehouseId !== 'ALL' && Number(item.warehouse_id) !== Number(selectedWarehouseId)) {
        return false;
      }

      // Filter by Status
      const status = getStockStatus(item);
      if (statusFilter !== 'ALL' && status !== statusFilter) {
        return false;
      }

      // Filter by Search Query
      if (!searchQuery.trim()) return true;
      const q = searchQuery.toLowerCase();
      const pName = item.product?.name?.toLowerCase() || '';
      const pSku = item.product?.sku?.toLowerCase() || '';
      const wName = item.warehouse?.name?.toLowerCase() || '';
      return pName.includes(q) || pSku.includes(q) || wName.includes(q);
    });
  }, [inventory, selectedWarehouseId, statusFilter, searchQuery]);

  const totalStockUnits = inventory.reduce((acc, item) => acc + (item.quantity || 0), 0);
  const lowStockCount = inventory.filter((item) => getStockStatus(item) === 'LOW_STOCK').length;
  const outOfStockCount = inventory.filter((item) => getStockStatus(item) === 'OUT_OF_STOCK').length;

  const handleOpenAdjust = (item) => {
    setModalState({ isOpen: true, mode: 'adjust', item });
  };

  const handleOpenTransfer = (item) => {
    setModalState({ isOpen: true, mode: 'transfer', item });
  };

  const handleOpenCreate = () => {
    setModalState({ isOpen: true, mode: 'create', item: null });
  };

  return (
    <div className="management-page" id="inventory-management-page">
      <PageHeader
        section="OPERATIONS CONTROL / INVENTORY"
        title="Inventory & Stock Balances"
        caption="Multi-hub stock levels, replenishments, warehouse reorders, and inter-facility stock transfers."
        metaPills={[
          { label: 'Total Units', value: totalStockUnits.toLocaleString() },
          { label: 'Low Stock', value: lowStockCount, status: lowStockCount > 0 ? 'warning' : 'online' },
          { label: 'Out of Stock', value: outOfStockCount, status: outOfStockCount > 0 ? 'error' : 'online' },
        ]}
        primaryAction={{
          label: 'Link Inventory',
          onClick: handleOpenCreate,
          requiredRoles: ['ADMIN', 'MANAGER'],
        }}
      />

      {error && (
        <div className="auth-alert error" style={{ marginBottom: '16px' }} role="alert">
          <div className="auth-alert-content">
            <span className="auth-alert-title">Unable to load inventory data</span>
            <span className="auth-alert-text">{error}</span>
          </div>
          <button type="button" className="btn-action outline" onClick={fetchData}>
            Retry
          </button>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="filter-controls-bar">
        <div className="search-input-wrapper">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <input
            type="search"
            className="table-search-input"
            placeholder="Search products, SKUs, or warehouses..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        {/* Warehouse Dropdown */}
        <select
          className="table-select-filter"
          value={selectedWarehouseId}
          onChange={(e) => setSelectedWarehouseId(e.target.value)}
        >
          <option value="ALL">All Warehouses ({warehouses.length})</option>
          {warehouses.map((wh) => (
            <option key={wh.id} value={wh.id}>
              {wh.name}
            </option>
          ))}
        </select>

        {/* Status Filters */}
        <div className="filter-tabs">
          <button
            type="button"
            className={`filter-tab ${statusFilter === 'ALL' ? 'active' : ''}`}
            onClick={() => setStatusFilter('ALL')}
          >
            All Items ({inventory.length})
          </button>
          <button
            type="button"
            className={`filter-tab ${statusFilter === 'HEALTHY' ? 'active' : ''}`}
            onClick={() => setStatusFilter('HEALTHY')}
          >
            Healthy ({inventory.length - lowStockCount - outOfStockCount})
          </button>
          <button
            type="button"
            className={`filter-tab ${statusFilter === 'LOW_STOCK' ? 'active' : ''}`}
            onClick={() => setStatusFilter('LOW_STOCK')}
          >
            Low Stock ({lowStockCount})
          </button>
          <button
            type="button"
            className={`filter-tab ${statusFilter === 'OUT_OF_STOCK' ? 'active' : ''}`}
            onClick={() => setStatusFilter('OUT_OF_STOCK')}
          >
            Depleted ({outOfStockCount})
          </button>
        </div>
      </div>

      {/* Inventory Table */}
      <div className="table-container">
        <table className="ops-table">
          <thead>
            <tr>
              <th>SKU / Code</th>
              <th>Product Details</th>
              <th>Warehouse Facility</th>
              <th>On-Hand Quantity</th>
              <th>Reorder Threshold</th>
              <th>Health Status</th>
              <th style={{ textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              [1, 2, 3, 4, 5].map((n) => (
                <tr key={n} className="skeleton-row">
                  <td colSpan="7">
                    <div className="skeleton-line" />
                  </td>
                </tr>
              ))
            ) : filteredInventory.length === 0 ? (
              <tr>
                <td colSpan="7" className="table-empty-cell">
                  <div className="empty-state-wrap">
                    <span className="empty-icon">📦</span>
                    <p className="empty-title">No inventory records found</p>
                    <p className="empty-desc">
                      {searchQuery
                        ? `No items matched "${searchQuery}".`
                        : 'No inventory allocated for this warehouse or filter.'}
                    </p>
                  </div>
                </td>
              </tr>
            ) : (
              filteredInventory.map((item) => {
                const status = getStockStatus(item);
                return (
                  <tr key={item.id}>
                    <td>
                      <span className="id-tag">{item.product?.sku || `PROD-${item.product_id}`}</span>
                    </td>
                    <td>
                      <div className="table-primary-text">{item.product?.name || `Product #${item.product_id}`}</div>
                    </td>
                    <td>
                      <span className="table-secondary-text">
                        {item.warehouse?.name || `Warehouse #${item.warehouse_id}`}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{ fontSize: '1rem', fontWeight: 700, color: status === 'OUT_OF_STOCK' ? '#F87171' : '#F1F5F9' }}>
                          {item.quantity.toLocaleString()}
                        </span>
                        <span style={{ fontSize: '0.75rem', color: '#64748B' }}>units</span>
                      </div>
                    </td>
                    <td>
                      <span className="table-secondary-text">{item.reorder_level} units</span>
                    </td>
                    <td>
                      <span
                        className={`status-badge ${
                          status === 'HEALTHY'
                            ? 'delivered'
                            : status === 'LOW_STOCK'
                            ? 'in-transit'
                            : 'failed'
                        }`}
                      >
                        {status.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      <div className="row-actions" style={{ justifyContent: 'flex-end', gap: '8px' }}>
                        {isManagerOrAdmin && (
                          <>
                            <button
                              type="button"
                              className="btn-action outline"
                              style={{ padding: '4px 10px', fontSize: '0.75rem' }}
                              onClick={() => handleOpenAdjust(item)}
                            >
                              Adjust Stock
                            </button>
                            <button
                              type="button"
                              className="btn-action outline"
                              style={{ padding: '4px 10px', fontSize: '0.75rem', borderColor: 'rgba(56, 189, 248, 0.4)', color: '#38BDF8' }}
                              onClick={() => handleOpenTransfer(item)}
                              disabled={item.quantity <= 0}
                              title={item.quantity <= 0 ? 'Cannot transfer 0 stock' : 'Transfer units to another warehouse'}
                            >
                              Transfer
                            </button>
                          </>
                        )}
                        {!isManagerOrAdmin && (
                          <span style={{ fontSize: '0.75rem', color: '#64748B' }}>Read-only</span>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Stock Adjust / Transfer / Create Modal */}
      <StockAdjustModal
        isOpen={modalState.isOpen}
        onClose={() => setModalState({ isOpen: false, mode: 'adjust', item: null })}
        mode={modalState.mode}
        item={modalState.item}
        warehouses={warehouses}
        products={products}
        onSuccess={fetchData}
      />
    </div>
  );
}
