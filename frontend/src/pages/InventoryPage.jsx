import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { inventoryApi } from '../api/inventory.js';
import { warehousesApi } from '../api/warehouses.js';
import { productsApi } from '../api/products.js';
import { formatErrorMessage } from '../api/client.js';
import { exportInventoryToCSV } from '../services/exportService.js';
import PageHeader from '../components/PageHeader';
import DataTable from '../components/DataTable';
import StatusBadge from '../components/StatusBadge';
import EmptyState from '../components/EmptyState';
import StockAdjustModal from '../components/StockAdjustModal';

export default function InventoryPage() {
  const { user } = useAuth();
  const { toast } = useToast();
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
    mode: 'adjust',
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

  const handleExportCSV = () => {
    try {
      const targetList = filteredInventory.length > 0 ? filteredInventory : inventory;
      const count = exportInventoryToCSV(targetList);
      toast.success(`Exported ${count} inventory records to CSV`);
    } catch (err) {
      toast.error(err.message || 'Failed to export inventory');
    }
  };

  const getStockStatus = (item) => {
    if (item.quantity === 0) return 'OUT_OF_STOCK';
    if (item.quantity <= (item.reorder_level || 10)) return 'LOW_STOCK';
    return 'HEALTHY';
  };

  const filteredInventory = useMemo(() => {
    return inventory.filter((item) => {
      if (selectedWarehouseId !== 'ALL' && Number(item.warehouse_id) !== Number(selectedWarehouseId)) {
        return false;
      }
      const status = getStockStatus(item);
      if (statusFilter !== 'ALL' && status !== statusFilter) {
        return false;
      }
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

  const handleSuccess = () => {
    toast.success('Inventory balance updated successfully');
    fetchData();
  };

  const columns = useMemo(() => [
    {
      key: 'sku',
      header: 'SKU / Code',
      sortable: true,
      render: (item) => (
        <span className="id-tag">{item.product?.sku || `PROD-${item.product_id}`}</span>
      ),
    },
    {
      key: 'product_name',
      header: 'Product Details',
      sortable: true,
      render: (item) => (
        <div className="table-primary-text">{item.product?.name || `Product #${item.product_id}`}</div>
      ),
    },
    {
      key: 'warehouse_name',
      header: 'Warehouse Facility',
      sortable: true,
      render: (item) => (
        <span className="table-secondary-text">
          {item.warehouse?.name || `Warehouse #${item.warehouse_id}`}
        </span>
      ),
    },
    {
      key: 'quantity',
      header: 'On-Hand Quantity',
      sortable: true,
      render: (item) => {
        const status = getStockStatus(item);
        return (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '1rem', fontWeight: 700, color: status === 'OUT_OF_STOCK' ? '#F87171' : '#F1F5F9' }}>
              {item.quantity.toLocaleString()}
            </span>
            <span style={{ fontSize: '0.75rem', color: '#64748B' }}>units</span>
          </div>
        );
      },
    },
    {
      key: 'reorder_level',
      header: 'Reorder Level',
      sortable: true,
      render: (item) => <span className="table-secondary-text">{item.reorder_level} units</span>,
    },
    {
      key: 'health',
      header: 'Stock Status',
      sortable: true,
      render: (item) => <StatusBadge status={getStockStatus(item)} />,
    },
    {
      key: 'actions',
      header: 'Actions',
      align: 'right',
      render: (item) => (
        <div className="row-actions" style={{ justifyContent: 'flex-end', gap: '8px' }}>
          {isManagerOrAdmin && (
            <>
              <button
                type="button"
                className="btn-action outline"
                style={{ padding: '4px 10px', fontSize: '0.75rem' }}
                onClick={(e) => {
                  e.stopPropagation();
                  handleOpenAdjust(item);
                }}
              >
                Adjust
              </button>
              <button
                type="button"
                className="btn-action outline"
                style={{ padding: '4px 10px', fontSize: '0.75rem', borderColor: 'rgba(56, 189, 248, 0.4)', color: '#38BDF8' }}
                onClick={(e) => {
                  e.stopPropagation();
                  handleOpenTransfer(item);
                }}
                disabled={item.quantity <= 0}
                title={item.quantity <= 0 ? 'Zero stock available' : 'Transfer units to another warehouse'}
              >
                Transfer
              </button>
            </>
          )}
          {!isManagerOrAdmin && (
            <span style={{ fontSize: '0.75rem', color: '#64748B' }}>Read-only</span>
          )}
        </div>
      ),
    },
  ], [isManagerOrAdmin]);

  return (
    <div className="management-page" id="inventory-management-page">
      <PageHeader
        section="OPERATIONS CONTROL / INVENTORY"
        title="Inventory & Stock Balances"
        caption="Multi-hub stock levels, replenishments, warehouse reorders, and inter-facility stock transfers."
        metaPills={[
          { label: 'Total Units', value: totalStockUnits.toLocaleString() },
          { label: 'Low Stock', value: lowStockCount, status: lowStockCount > 0 ? 'warning' : 'online' },
          { label: 'Out of Stock', value: outOfStockCount, status: outOfStockCount > 0 ? 'danger' : 'online' },
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
          <option value="ALL">All Facilities ({warehouses.length})</option>
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

        <button
          type="button"
          className="fg-export-btn"
          onClick={handleExportCSV}
          title="Download filtered inventory as CSV spreadsheet"
          disabled={loading || inventory.length === 0}
        >
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="7 10 12 15 17 10" />
            <line x1="12" y1="15" x2="12" y2="3" />
          </svg>
          <span>Export CSV</span>
        </button>
      </div>

      {/* Reusable Data Table */}
      <DataTable
        columns={columns}
        data={filteredInventory}
        loading={loading}
        pageSize={10}
        keyField="id"
        emptyState={
          <EmptyState
            icon="📦"
            title="No inventory records found"
            description={
              searchQuery
                ? `No items matched query "${searchQuery}".`
                : 'No inventory allocated for this facility or status filter.'
            }
            action={{
              label: 'Allocate Product Stock',
              onClick: handleOpenCreate,
              requiredRoles: ['ADMIN', 'MANAGER'],
            }}
          />
        }
      />

      {/* Stock Adjust / Transfer / Create Modal */}
      <StockAdjustModal
        isOpen={modalState.isOpen}
        onClose={() => setModalState({ isOpen: false, mode: 'adjust', item: null })}
        mode={modalState.mode}
        item={modalState.item}
        warehouses={warehouses}
        products={products}
        onSuccess={handleSuccess}
      />
    </div>
  );
}
