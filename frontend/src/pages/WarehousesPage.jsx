import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { warehousesApi } from '../api/warehouses.js';
import { formatErrorMessage } from '../api/client.js';
import PageHeader from '../components/PageHeader';
import DataTable from '../components/DataTable';
import StatusBadge from '../components/StatusBadge';
import EmptyState from '../components/EmptyState';
import ConfirmDialog from '../components/ConfirmDialog';
import WarehouseModal from '../components/WarehouseModal';

export default function WarehousesPage() {
  const { user } = useAuth();
  const { toast } = useToast();
  const isAdmin = user?.role === 'ADMIN';
  const isManagerOrAdmin = user?.role === 'ADMIN' || user?.role === 'MANAGER';

  const [warehouses, setWarehouses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL'); // 'ALL' | 'ACTIVE' | 'INACTIVE'
  const [selectedWarehouse, setSelectedWarehouse] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Deactivation confirmation modal state
  const [deactivatingWarehouse, setDeactivatingWarehouse] = useState(null);
  const [isDeactivating, setIsDeactivating] = useState(false);

  const fetchWarehouses = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await warehousesApi.listWarehouses({ limit: 200 });
      setWarehouses(data || []);
    } catch (err) {
      setError(formatErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchWarehouses();
  }, [fetchWarehouses]);

  const filteredWarehouses = useMemo(() => {
    return warehouses.filter((wh) => {
      if (statusFilter === 'ACTIVE' && !wh.is_active) return false;
      if (statusFilter === 'INACTIVE' && wh.is_active) return false;
      if (!searchQuery.trim()) return true;
      const q = searchQuery.toLowerCase();
      return (
        wh.name.toLowerCase().includes(q) ||
        wh.location.toLowerCase().includes(q) ||
        wh.address.toLowerCase().includes(q)
      );
    });
  }, [warehouses, statusFilter, searchQuery]);

  const handleOpenCreate = () => {
    setSelectedWarehouse(null);
    setIsModalOpen(true);
  };

  const handleOpenEdit = (wh) => {
    setSelectedWarehouse(wh);
    setIsModalOpen(true);
  };

  const handleConfirmDeactivate = async () => {
    if (!isAdmin || !deactivatingWarehouse) return;
    setIsDeactivating(true);
    try {
      await warehousesApi.deleteWarehouse(deactivatingWarehouse.id);
      toast.warning(`Warehouse facility "${deactivatingWarehouse.name}" deactivated`);
      setDeactivatingWarehouse(null);
      fetchWarehouses();
    } catch (err) {
      toast.error(formatErrorMessage(err));
    } finally {
      setIsDeactivating(false);
    }
  };

  const handleSaved = (wh, isEdit) => {
    toast.success(`Warehouse "${wh.name}" ${isEdit ? 'updated' : 'registered'} successfully`);
    fetchWarehouses();
  };

  const activeCount = warehouses.filter((w) => w.is_active).length;
  const totalCapacity = warehouses.reduce((acc, w) => acc + (w.capacity || 0), 0);

  const columns = useMemo(() => [
    {
      key: 'id',
      header: 'Facility ID',
      sortable: true,
      render: (wh) => <span className="id-tag">WH-{wh.id}</span>,
    },
    {
      key: 'name',
      header: 'Name & Hub',
      sortable: true,
      render: (wh) => <div className="table-primary-text">{wh.name}</div>,
    },
    {
      key: 'location',
      header: 'Metropolitan Area',
      sortable: true,
      render: (wh) => <span className="table-secondary-text">{wh.location}</span>,
    },
    {
      key: 'address',
      header: 'Street Address',
      render: (wh) => (
        <span className="table-secondary-text" style={{ maxWidth: '240px', display: 'inline-block' }}>
          {wh.address}
        </span>
      ),
    },
    {
      key: 'capacity',
      header: 'Capacity',
      sortable: true,
      render: (wh) => (
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <span style={{ fontWeight: 600, color: '#F1F5F9' }}>
            {wh.capacity ? wh.capacity.toLocaleString() : '0'} units
          </span>
          <span style={{ fontSize: '0.72rem', color: '#64748B' }}>Pallet storage</span>
        </div>
      ),
    },
    {
      key: 'is_active',
      header: 'Status',
      sortable: true,
      render: (wh) => <StatusBadge status={wh.is_active ? 'OPERATIONAL' : 'INACTIVE'} />,
    },
    {
      key: 'actions',
      header: 'Actions',
      align: 'right',
      render: (wh) => (
        <div className="row-actions" style={{ justifyContent: 'flex-end', gap: '8px' }}>
          {isManagerOrAdmin && (
            <button
              type="button"
              className="btn-action outline"
              style={{ padding: '4px 10px', fontSize: '0.75rem' }}
              onClick={(e) => {
                e.stopPropagation();
                handleOpenEdit(wh);
              }}
            >
              Edit
            </button>
          )}
          {isAdmin && wh.is_active && (
            <button
              type="button"
              className="btn-action outline"
              style={{ padding: '4px 10px', fontSize: '0.75rem', borderColor: 'rgba(239, 68, 68, 0.4)', color: '#F87171' }}
              onClick={(e) => {
                e.stopPropagation();
                setDeactivatingWarehouse(wh);
              }}
            >
              Deactivate
            </button>
          )}
          {!isManagerOrAdmin && (
            <button
              type="button"
              className="btn-action outline"
              style={{ padding: '4px 10px', fontSize: '0.75rem' }}
              onClick={(e) => {
                e.stopPropagation();
                handleOpenEdit(wh);
              }}
            >
              View
            </button>
          )}
        </div>
      ),
    },
  ], [isAdmin, isManagerOrAdmin]);

  return (
    <div className="management-page" id="warehouses-management-page">
      <PageHeader
        section="OPERATIONS CONTROL / FACILITIES"
        title="Warehouse Facilities"
        caption="Manage fulfillment centers, distribution hubs, storage capacities, and operational depots."
        metaPills={[
          { label: 'Total Hubs', value: warehouses.length },
          { label: 'Operational', value: activeCount, status: 'online' },
          { label: 'Total Pallets', value: totalCapacity.toLocaleString() },
        ]}
        primaryAction={{
          label: 'Register Warehouse',
          onClick: handleOpenCreate,
          requiredRoles: ['ADMIN', 'MANAGER'],
        }}
      />

      {error && (
        <div className="auth-alert error" style={{ marginBottom: '16px' }} role="alert">
          <div className="auth-alert-content">
            <span className="auth-alert-title">Unable to load warehouses</span>
            <span className="auth-alert-text">{error}</span>
          </div>
          <button type="button" className="btn-action outline" onClick={fetchWarehouses}>
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
            placeholder="Search warehouses by name, region, or address..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        <div className="filter-tabs">
          <button
            type="button"
            className={`filter-tab ${statusFilter === 'ALL' ? 'active' : ''}`}
            onClick={() => setStatusFilter('ALL')}
          >
            All Facilities ({warehouses.length})
          </button>
          <button
            type="button"
            className={`filter-tab ${statusFilter === 'ACTIVE' ? 'active' : ''}`}
            onClick={() => setStatusFilter('ACTIVE')}
          >
            Active ({activeCount})
          </button>
          <button
            type="button"
            className={`filter-tab ${statusFilter === 'INACTIVE' ? 'active' : ''}`}
            onClick={() => setStatusFilter('INACTIVE')}
          >
            Inactive ({warehouses.length - activeCount})
          </button>
        </div>
      </div>

      {/* Reusable Data Table */}
      <DataTable
        columns={columns}
        data={filteredWarehouses}
        loading={loading}
        pageSize={10}
        keyField="id"
        emptyState={
          <EmptyState
            icon="🏭"
            title="No warehouse facilities found"
            description={
              searchQuery
                ? `No facilities matched query "${searchQuery}".`
                : 'No facilities registered in this status filter.'
            }
            action={{
              label: 'Register Warehouse',
              onClick: handleOpenCreate,
              requiredRoles: ['ADMIN', 'MANAGER'],
            }}
          />
        }
      />

      {/* Warehouse Create / Edit Modal */}
      <WarehouseModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        warehouse={selectedWarehouse}
        onSaved={handleSaved}
      />

      {/* Confirm Deactivation Dialog */}
      <ConfirmDialog
        isOpen={Boolean(deactivatingWarehouse)}
        title="Deactivate Warehouse Facility"
        message={
          deactivatingWarehouse ? (
            <span>
              Are you sure you want to deactivate <strong>{deactivatingWarehouse.name}</strong>?
              Inactive facilities cannot receive new inventory or act as departure origins for shipments.
            </span>
          ) : ''
        }
        confirmLabel="Yes, Deactivate"
        cancelLabel="Cancel"
        confirmVariant="danger"
        isLoading={isDeactivating}
        onConfirm={handleConfirmDeactivate}
        onCancel={() => setDeactivatingWarehouse(null)}
      />
    </div>
  );
}
