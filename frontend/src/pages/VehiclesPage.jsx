import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useAuth } from '../context/AuthContext';
import { vehiclesApi } from '../api/vehicles.js';
import { formatErrorMessage } from '../api/client.js';
import PageHeader from '../components/PageHeader';
import VehicleModal from '../components/VehicleModal';

export default function VehiclesPage() {
  const { user } = useAuth();
  const isManagerOrAdmin = user?.role === 'ADMIN' || user?.role === 'MANAGER';

  const [vehicles, setVehicles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL'); // 'ALL' | 'AVAILABLE' | 'IN_USE' | 'MAINTENANCE' | 'DECOMMISSIONED'

  // Modal control
  const [modalState, setModalState] = useState({
    isOpen: false,
    vehicle: null,
    isStatusOnly: false,
  });

  const fetchVehicles = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await vehiclesApi.listVehicles({ limit: 150 });
      setVehicles(data || []);
    } catch (err) {
      setError(formatErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchVehicles();
  }, [fetchVehicles]);

  const filteredVehicles = useMemo(() => {
    return vehicles.filter((veh) => {
      if (statusFilter !== 'ALL' && veh.status !== statusFilter) {
        return false;
      }
      if (!searchQuery.trim()) return true;
      const q = searchQuery.toLowerCase();
      const reg = veh.registration_number?.toLowerCase() || '';
      const type = veh.vehicle_type?.toLowerCase() || '';
      return reg.includes(q) || type.includes(q);
    });
  }, [vehicles, statusFilter, searchQuery]);

  const availableCount = vehicles.filter((v) => v.status === 'AVAILABLE').length;
  const inUseCount = vehicles.filter((v) => v.status === 'IN_USE').length;
  const maintenanceCount = vehicles.filter((v) => v.status === 'MAINTENANCE').length;

  const handleOpenRegister = () => {
    setModalState({ isOpen: true, vehicle: null, isStatusOnly: false });
  };

  const handleOpenEdit = (veh) => {
    setModalState({ isOpen: true, vehicle: veh, isStatusOnly: false });
  };

  const handleOpenStatus = (veh) => {
    setModalState({ isOpen: true, vehicle: veh, isStatusOnly: true });
  };

  return (
    <div className="management-page" id="vehicles-management-page">
      <PageHeader
        section="OPERATIONS CONTROL / FLEET"
        title="Fleet Vehicles"
        caption="Manage semi-trailers, box trucks, cargo vans, carrying capacities, and maintenance schedules."
        metaPills={[
          { label: 'Total Fleet', value: vehicles.length },
          { label: 'Available', value: availableCount, status: 'online' },
          { label: 'In Service', value: inUseCount, status: 'in-transit' },
          { label: 'Workshop', value: maintenanceCount, status: maintenanceCount > 0 ? 'warning' : 'online' },
        ]}
        primaryAction={{
          label: 'Register Asset',
          onClick: handleOpenRegister,
          requiredRoles: ['ADMIN', 'MANAGER'],
        }}
      />

      {error && (
        <div className="auth-alert error" style={{ marginBottom: '16px' }} role="alert">
          <div className="auth-alert-content">
            <span className="auth-alert-title">Unable to load fleet vehicles</span>
            <span className="auth-alert-text">{error}</span>
          </div>
          <button type="button" className="btn-action outline" onClick={fetchVehicles}>
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
            placeholder="Search vehicles by registration plate, type, or model..."
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
            All Fleet ({vehicles.length})
          </button>
          <button
            type="button"
            className={`filter-tab ${statusFilter === 'AVAILABLE' ? 'active' : ''}`}
            onClick={() => setStatusFilter('AVAILABLE')}
          >
            Available ({availableCount})
          </button>
          <button
            type="button"
            className={`filter-tab ${statusFilter === 'IN_USE' ? 'active' : ''}`}
            onClick={() => setStatusFilter('IN_USE')}
          >
            In Use ({inUseCount})
          </button>
          <button
            type="button"
            className={`filter-tab ${statusFilter === 'MAINTENANCE' ? 'active' : ''}`}
            onClick={() => setStatusFilter('MAINTENANCE')}
          >
            Maintenance ({maintenanceCount})
          </button>
        </div>
      </div>

      {/* Vehicles Table */}
      <div className="table-container">
        <table className="ops-table">
          <thead>
            <tr>
              <th>Vehicle ID</th>
              <th>Registration Plate</th>
              <th>Type Classification</th>
              <th>Payload Capacity</th>
              <th>Operational Status</th>
              <th style={{ textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              [1, 2, 3, 4].map((n) => (
                <tr key={n} className="skeleton-row">
                  <td colSpan="6">
                    <div className="skeleton-line" />
                  </td>
                </tr>
              ))
            ) : filteredVehicles.length === 0 ? (
              <tr>
                <td colSpan="6" className="table-empty-cell">
                  <div className="empty-state-wrap">
                    <span className="empty-icon">🚛</span>
                    <p className="empty-title">No fleet vehicles found</p>
                    <p className="empty-desc">
                      {searchQuery
                        ? `No vehicles matched query "${searchQuery}".`
                        : 'No fleet vehicles found matching selected status filter.'}
                    </p>
                  </div>
                </td>
              </tr>
            ) : (
              filteredVehicles.map((veh) => (
                <tr key={veh.id}>
                  <td>
                    <span className="id-tag">VEH-{veh.id}</span>
                  </td>
                  <td>
                    <span style={{ fontFamily: 'monospace', fontWeight: 600, color: '#F1F5F9' }}>
                      {veh.registration_number}
                    </span>
                  </td>
                  <td>
                    <span className="table-primary-text">{veh.vehicle_type}</span>
                  </td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span style={{ fontWeight: 600, color: '#F1F5F9' }}>
                        {Number(veh.capacity).toLocaleString()}
                      </span>
                      <span style={{ fontSize: '0.72rem', color: '#64748B' }}>kg max payload</span>
                    </div>
                  </td>
                  <td>
                    <span
                      className={`status-badge ${
                        veh.status === 'AVAILABLE'
                          ? 'delivered'
                          : veh.status === 'IN_USE'
                          ? 'in-transit'
                          : veh.status === 'MAINTENANCE'
                          ? 'failed'
                          : 'cancelled'
                      }`}
                    >
                      {veh.status}
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
                            onClick={() => handleOpenStatus(veh)}
                          >
                            Status
                          </button>
                          <button
                            type="button"
                            className="btn-action outline"
                            style={{ padding: '4px 10px', fontSize: '0.75rem' }}
                            onClick={() => handleOpenEdit(veh)}
                          >
                            Edit
                          </button>
                        </>
                      )}
                      {!isManagerOrAdmin && (
                        <span style={{ fontSize: '0.75rem', color: '#64748B' }}>Read-only</span>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Vehicle Modal */}
      <VehicleModal
        isOpen={modalState.isOpen}
        onClose={() => setModalState({ isOpen: false, vehicle: null, isStatusOnly: false })}
        vehicle={modalState.vehicle}
        isStatusOnly={modalState.isStatusOnly}
        onSaved={fetchVehicles}
      />
    </div>
  );
}
