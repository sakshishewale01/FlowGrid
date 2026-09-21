import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useAuth } from '../context/AuthContext';
import { warehousesApi } from '../api/warehouses.js';
import { formatErrorMessage } from '../api/client.js';
import PageHeader from '../components/PageHeader';
import WarehouseModal from '../components/WarehouseModal';

export default function WarehousesPage() {
  const { user } = useAuth();
  const isAdmin = user?.role === 'ADMIN';
  const isManagerOrAdmin = user?.role === 'ADMIN' || user?.role === 'MANAGER';

  const [warehouses, setWarehouses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL'); // 'ALL' | 'ACTIVE' | 'INACTIVE'
  const [selectedWarehouse, setSelectedWarehouse] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [deleteError, setDeleteError] = useState(null);

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

  const handleDelete = async (wh) => {
    if (!isAdmin) return;
    if (!window.confirm(`Are you sure you want to deactivate warehouse "${wh.name}"?`)) return;

    setDeleteError(null);
    try {
      await warehousesApi.deleteWarehouse(wh.id);
      fetchWarehouses();
    } catch (err) {
      setDeleteError(formatErrorMessage(err));
    }
  };

  const handleSaved = () => {
    fetchWarehouses();
  };

  const activeCount = warehouses.filter((w) => w.is_active).length;
  const totalCapacity = warehouses.reduce((acc, w) => acc + (w.capacity || 0), 0);

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

      {deleteError && (
        <div className="auth-alert error" style={{ marginBottom: '16px' }}>
          <span className="auth-alert-text">{deleteError}</span>
        </div>
      )}

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

      {/* Facilities Table */}
      <div className="table-container">
        <table className="ops-table">
          <thead>
            <tr>
              <th>Facility ID</th>
              <th>Name & Code</th>
              <th>Metropolitan Area</th>
              <th>Address</th>
              <th>Capacity</th>
              <th>Status</th>
              <th style={{ textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              [1, 2, 3, 4].map((n) => (
                <tr key={n} className="skeleton-row">
                  <td colSpan="7">
                    <div className="skeleton-line" />
                  </td>
                </tr>
              ))
            ) : filteredWarehouses.length === 0 ? (
              <tr>
                <td colSpan="7" className="table-empty-cell">
                  <div className="empty-state-wrap">
                    <span className="empty-icon">🏭</span>
                    <p className="empty-title">No warehouse facilities found</p>
                    <p className="empty-desc">
                      {searchQuery
                        ? `No facilities matched query "${searchQuery}".`
                        : 'No facilities registered in this status filter.'}
                    </p>
                  </div>
                </td>
              </tr>
            ) : (
              filteredWarehouses.map((wh) => (
                <tr key={wh.id}>
                  <td>
                    <span className="id-tag">WH-{wh.id}</span>
                  </td>
                  <td>
                    <div className="table-primary-text">{wh.name}</div>
                  </td>
                  <td>
                    <span className="table-secondary-text">{wh.location}</span>
                  </td>
                  <td>
                    <span className="table-secondary-text" style={{ maxWidth: '240px', display: 'inline-block' }}>
                      {wh.address}
                    </span>
                  </td>
                  <td>
                    <div style={{ display: 'flex', flexDirection: 'column' }}>
                      <span style={{ fontWeight: 600, color: '#F1F5F9' }}>
                        {wh.capacity ? wh.capacity.toLocaleString() : '0'} units
                      </span>
                      <span style={{ fontSize: '0.72rem', color: '#64748B' }}>Pallet storage</span>
                    </div>
                  </td>
                  <td>
                    <span className={`status-badge ${wh.is_active ? 'delivered' : 'cancelled'}`}>
                      {wh.is_active ? 'OPERATIONAL' : 'INACTIVE'}
                    </span>
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <div className="row-actions" style={{ justifyContent: 'flex-end', gap: '8px' }}>
                      {isManagerOrAdmin && (
                        <button
                          type="button"
                          className="btn-action outline"
                          style={{ padding: '4px 10px', fontSize: '0.75rem' }}
                          onClick={() => handleOpenEdit(wh)}
                        >
                          Edit
                        </button>
                      )}
                      {isAdmin && (
                        <button
                          type="button"
                          className="btn-action outline"
                          style={{ padding: '4px 10px', fontSize: '0.75rem', borderColor: 'rgba(239, 68, 68, 0.4)', color: '#F87171' }}
                          onClick={() => handleDelete(wh)}
                        >
                          Deactivate
                        </button>
                      )}
                      {!isManagerOrAdmin && (
                        <button
                          type="button"
                          className="btn-action outline"
                          style={{ padding: '4px 10px', fontSize: '0.75rem' }}
                          onClick={() => handleOpenEdit(wh)}
                        >
                          View
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Warehouse Create / Edit Modal */}
      <WarehouseModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        warehouse={selectedWarehouse}
        onSaved={handleSaved}
      />
    </div>
  );
}
